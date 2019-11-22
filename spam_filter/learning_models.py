import logging
import math
import numpy as np
import pickle
from abc import ABC, abstractmethod
from collections import defaultdict, Counter
from itertools import chain, islice
from typing import List, Tuple, Union, Iterable as TIterable, Optional

from cacheops import invalidate_model, invalidate_obj
from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from keras.metrics import binary_accuracy
from keras.models import Sequential
from keras.layers import Dense, Dropout
from pathos.multiprocessing import ProcessPool as Pool

from spam_filter.content_parser import ContentParser
from spam_filter.mail_source import MailContentSource
from spam_filter.models import BayesDictionary, NNStructure

logger = logging.getLogger('default')


class LearningModel(ABC):

    @classmethod
    def train(cls, spam: Optional[MailContentSource] = None, ham: Optional[MailContentSource] = None,
              init: bool = False, batch_size: int = 1000, **kwargs):
        assert spam or ham, 'One of spam or ham should be provided'

        learning_content = chain(((content, True) for content in spam.get_content()) if spam else (),
                                 ((content, False) for content in ham.get_content()) if ham else ())

        iterator = iter(learning_content)
        first = True

        while True:
            init = True if init and first else False
            content = list(islice(iterator, batch_size))
            cls._train(content, init=init, **kwargs)
            first = False

            if len(content) < batch_size:
                break

    @classmethod
    @abstractmethod
    def _train(cls, *args, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def check_message_for_spam(cls, message: str, **kwargs) -> bool:
        pass

    @classmethod
    def check_for_valid(cls, spam: MailContentSource, ham: MailContentSource, num_msg_to_check: int = 100, **kwargs) \
            -> List[Tuple[str, bool]]:
        """
        Проверяет модель на валидность и возвращает список сообщений, которые неправильно идентифицированы
        как спам или наоборот - хам идентифицирован как спам
        :param spam: MailContentSource со спамом
        :param ham: MailContentSource с хамом
        :param num_msg_to_check: Число сообщений попадающих в выборку
        :return: Список, содержащий ошибочно определенные сообщения. (сообщение, predicted_spam_flag)
        """
        errors = []

        def _check_for_errors(content: TIterable[str], spam_flag: bool):
            for index, msg in enumerate(content):
                logger.info('Proccess record: %d in %s spam dictionary' % (index, spam_flag))

                if spam_flag != cls.check_message_for_spam(msg, **kwargs):
                    errors.append((msg, spam_flag))

        _check_for_errors(spam.get_content(max_items=num_msg_to_check), True)
        _check_for_errors(ham.get_content(max_items=num_msg_to_check), False)

        return errors


class BayesModel(LearningModel):

    @classmethod
    def train(cls, spam: Optional[MailContentSource] = None, ham: Optional[MailContentSource] = None,
              init: bool = False, batch_size: int = 1000, min_num_word_appearance: int = 1):
        """
        Тренируем модель используя источники спам и хам писем MailContentSource
        :param spam: MailContentSource со спамом
        :param ham: MailContentSource с хамом
        :param min_num_word_appearance: Минимальное количество встречаемости слова для попадания в словарь
        :param init: Если параметр установлен, то удаляет предыдущий словарь и инициализирует новый. Если нет,
        то обучает старый словарь
        :param batch_size: Размер порции обучения
        :return: None
        """
        return super().train(spam, ham, init=init, batch_size=batch_size,
                             min_num_word_appearance=min_num_word_appearance)

    @staticmethod
    def _train_parse(iterable_variables) -> Optional[defaultdict]:
        index, (msg, spam) = iterable_variables
        dictionary = defaultdict(lambda: [0, 0, 0])
        value_list_index = 1 if spam else 2
        words = set(word for word in ContentParser.parse(msg).split(' ') if len(word) > 2) if msg else {}

        if words:
            logger.info('Proccess message N: %d' % index)
            for word in words:
                dictionary[word][0] += 1
                dictionary[word][value_list_index] += 1

            return dictionary

    @classmethod
    def _train(cls, learning_content: Union[TIterable[Tuple[str, bool]], Tuple[str, bool]],
               min_num_word_appearance: int = 1, init: bool = False) -> None:
        """
        Обучает словарь по сообщениям из learning_content
        :param learning_content: список с Tuple или Tuple внутри которого сообщение и флаг спам или нет
        :param min_num_word_appearance: Минимальное количество встречаемости слова для попадания в словарь
        :param init: Если параметр установлен, то удаляет предыдущий словарь и инициализирует новый. Если нет,
        то обучает старый словарь
        :return: None
        """
        if isinstance(learning_content, tuple):
            learning_content = [learning_content]

        # word - ключ, value[0] - всего, value[1] - появлений в spam, value[2] - появлений в ham
        dictionary = defaultdict(lambda: [0, 0, 0])

        with Pool(processes=settings.NUM_CPU_CORES) as pool:
            results = ((k, v) for item in pool.map(cls._train_parse, enumerate(learning_content)) if item
                       for k, v in item.items())

        for k, v in results:
            dictionary[k] = list(map(lambda x, y: x + y, dictionary[k], v))

        updates = [{
            'word': word,
            'spam_count': values[1],
            'ham_count': values[2]
        } for word, values in dictionary.items() if values[0] >= min_num_word_appearance]

        def on_commit(items, init_flag):
            if init_flag:
                invalidate_model(BayesDictionary)
            else:
                # у запроса aggregate также сбросится кэш при сбрасывании кэша одной записи
                for instance in items:
                    invalidate_obj(instance)

        if updates:
            with transaction.atomic():
                if init:
                    BayesDictionary.objects.all().delete()
                    update_words = None
                else:
                    update_words = list(BayesDictionary.objects.filter(word__in=[item['word'] for item in updates])
                                        .select_for_update())

                BayesDictionary.objects.bulk_update_or_create(updates, key_fields='word',
                                                              set_functions={'spam_count': '+', 'ham_count': '+'})
                transaction.on_commit(lambda: on_commit(update_words, init))

    @classmethod
    def check_message_for_spam(cls, message: str, return_probability: bool = False, clear_body: bool = False) \
            -> Union[int, bool]:
        """
        Проверяет сообщение на спам
        :param message: Сообщение, которое проверяется на спам
        :param return_probability: вернуть вероятность, вместо флага True/False
        :param clear_body: Было ли содержимое предварительно обработано
        :return: boolean. Спам или нет
        """
        parse_content = message if clear_body else ContentParser.parse(message)
        words = {item for item in parse_content.split(' ')}

        # все запросы к BayesDictionary кэшируются на сутки или до нового обучения словаря.
        aggr_sum = BayesDictionary.objects.aggregate(sum_spam=Sum('spam_count'), sum_ham=Sum('ham_count'))
        qs = BayesDictionary.objects.filter(word__in=words).values_list('word', 'spam_count', 'ham_count')
        word_dict = {item[0]: (item[1], item[2]) for item in qs}

        prob_word_spam = {word: (spam_freq / aggr_sum['sum_spam']) /
                                ((spam_freq / aggr_sum['sum_spam']) + (ham_freq / aggr_sum['sum_ham']))
                          for word, (spam_freq, ham_freq) in word_dict.items()}

        # n - количество учитываемых максимальных отклонений вероятности спамовости от 0.5
        n = 13
        max_prob_words = Counter()

        for word, probability in prob_word_spam.items():
            max_prob_words[word] = math.fabs((0.5 - probability))

        # p = p1p2p3...pn/(p1p2...pn + (1-p1)(1-p2)..(1-pn)), где pi - вероятность, что слово(i)-спам,
        # p - вероятность, что сообщение - спам
        multiple_spam_prob = 1
        multiple_ham_prob = 1

        for word, _ in max_prob_words.most_common(n):
            # Сглаживающая формула Pr(S|W) = (s*Pr(s) + n*Pr(S|W))/s+n
            s = 3  # должно быть s повторений слова в словаре, чтобы повысить к нему доверие
            word_occur = word_dict[word][0] + word_dict[word][1]
            spam_prob = (s * 0.5 + word_occur * prob_word_spam[word]) / (s + word_occur)

            multiple_spam_prob *= spam_prob
            multiple_ham_prob *= 1 - spam_prob

        spam_probability = multiple_spam_prob / (multiple_spam_prob + multiple_ham_prob)

        return spam_probability if return_probability else spam_probability > 0.9


class NN(LearningModel):
    num_metrics = 7

    @classmethod
    def _update_model(cls, model: Sequential):
        weights = pickle.dumps(model.get_weights())
        NNStructure.objects.update_or_create(defaults={'weights': weights})

    @classmethod
    def _get_model(cls, init: bool = False) -> Sequential:
        """
        Пытается получить модель из БД или инициализирует новую
        :param init: Если False - попытаться получить модель из БД
        :return: Объект Sequential нейросети
        """
        model = Sequential()
        model.add(Dense(128, activation='relu', input_shape=(cls.num_metrics,)))
        model.add(Dropout(0.5))
        model.add(Dense(64, activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(1, activation='sigmoid'))
        model.summary()
        model.compile(loss='binary_crossentropy',
                      optimizer='adam',
                      metrics=['acc', binary_accuracy])

        if not init:
            weights = pickle.dumps(model.get_weights())
            nn_struct, created = NNStructure.objects.get_or_create(weights=weights)

            if not created:
                model.set_weights(pickle.loads(nn_struct.weights))

        return model

    @staticmethod
    def _train_parse(iterable_variables) -> Optional[Tuple]:
        index, (msg, spam) = iterable_variables
        prepared_data = ContentParser.prepare_for_pnn(msg)

        if prepared_data:
            parsed_body, msg_info = prepared_data
            bayes_prob = BayesModel.check_message_for_spam(parsed_body, return_probability=True, clear_body=True)
            logger.info('Proccessed message N: %d' % index)

            return (*msg_info, bayes_prob), spam

    @classmethod
    def _train(cls, learning_content: Union[TIterable[Tuple[str, bool]], Tuple[str, bool]], init: bool = False):
        """
        Обучает нейронную сеть используя learning_content
        :param learning_content: список с Tuple или Tuple внутри которого сообщение и флаг спам или нет
        :param init: Если параметр установлен, то удаляет предыдущий словарь и инициализирует новый. Если нет,
        то обучает старый словарь
        :return: None
        """
        if isinstance(learning_content, tuple):
            learning_content = [learning_content]

        # Костыль, но более внятного решения проблемы коннекта к БД при multiprocessing не нашел
        from django.db import connections
        connections.close_all()

        with Pool(processes=settings.NUM_CPU_CORES) as pool:
            results = (item for item in pool.map(cls._train_parse, enumerate(learning_content)) if item)

        # X - вход. Пустой np.array, который динамически заполнится далее
        x = np.empty((0, cls.num_metrics), dtype=np.float64)
        y = np.empty((0, 1), dtype=np.float64)
        num_msgs = 0

        for x_inp, y_inp in results:
            x = np.append(x, np.array([x_inp]), axis=0)
            y = np.append(y, np.array([y_inp], dtype=np.float64))
            num_msgs += 1

        y = y.reshape(-1, 1)

        epochs = num_msgs * 3
        model = cls._get_model(init=init)
        model.fit(x, y, batch_size=num_msgs, epochs=epochs, verbose=1, shuffle=True, validation_split=0.2)
        cls._update_model(model)

    @classmethod
    def check_for_valid(cls, spam: MailContentSource, ham: MailContentSource, num_msg_to_check: int = 100,
                        **kwargs) -> List[Tuple[str, bool]]:
        nn = cls._get_model()
        return super().check_for_valid(spam, ham, num_msg_to_check=num_msg_to_check, nn=nn)

    @classmethod
    def check_message_for_spam(cls, message: str, nn: Sequential = None) -> bool:
        """
        Проверяет сообщение на спам
        :param message: Сообщение
        :param nn: Опционально, экземпляр модели нейросети, чтобы не получать ее каждый раз из БД
        :return: boolean. Сообщение спам или нет
        """
        prepared_data = ContentParser.prepare_for_pnn(message)

        if prepared_data:
            nn = nn or cls._get_model()
            parsed_body, msg_info = prepared_data
            bayes_prob = BayesModel.check_message_for_spam(parsed_body, return_probability=True, clear_body=True)
            result = nn.predict(np.array([(*msg_info, bayes_prob)]))

            # При сравнении возвращается nparray([[boolean]]). Приведем к bool
            return bool(result > 0.6)
        else:
            return False
