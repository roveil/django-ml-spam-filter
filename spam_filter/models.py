import logging
import math
from collections import defaultdict, Counter
from itertools import chain
from typing import List, Tuple, Union, Iterable as TIterable

from cacheops import invalidate_model, invalidate_obj
from django.db import models, transaction
from django.db.models import Sum
from django_pg_bulk_update.manager import BulkUpdateManager

from spam_filter.content_parser import ContentParser

logger = logging.getLogger('default')


class LearningMessage(models.Model):
    message = models.TextField()
    spam = models.BooleanField()
    processed = models.DateTimeField(null=True, blank=True)


class Dictionary(models.Model):
    word = models.CharField(max_length=255, db_index=True, unique=True)
    spam_count = models.PositiveIntegerField(default=0)
    ham_count = models.PositiveIntegerField(default=0)

    objects = BulkUpdateManager()

    @classmethod
    def init_dictionary_from_files(cls, spam_file_path: str, ham_file_path: str, delimiter: str, learn_words_num: int,
                                   init: bool = True) -> None:
        """
        Инициализирует словарь используя файл с письмами со спамом и файл с письмами без спама.
        Типичная запись в файле
        **********
        <p>Сколько человек будут проживать?</p>
        **********
        :param spam_file_path: Путь до файла с письмами со спамом
        :param ham_file_path: Путь до файла с письмами без спама.
        :param delimiter: Разделитель содержимого внутри файла. В примере - **********\n
        :param learn_words_num: Количество самых популярных слов, которые необходимо изучить
        :param init: Если параметр установлен, то удаляет предыдущий словарь и инициализирует новый. Если нет,
        то обучает старый словарь
        :return: None
        """

        def _get_content_from_file(filename: str):
            with open(filename, 'r') as f:
                return f.read().split(delimiter)

        spam_content = _get_content_from_file(spam_file_path)
        ham_content = _get_content_from_file(ham_file_path)

        learning_content = chain(((content, True) for content in spam_content),
                                 ((content, False) for content in ham_content))

        cls.train_dictionary(learning_content, learn_words_num=learn_words_num, init=init)

    @classmethod
    def train_dictionary(cls, learning_content: Union[TIterable[Tuple[str, bool]], Tuple[str, bool]],
                         learn_words_num: int = 20, init: bool = False) -> None:
        """
        Обучает словарь по сообщениям из learning_content
        :param learning_content: список с Tuple внутри которого список с сообщениями и флаг спам или нет
        :param learn_words_num: Количество самых популярных слов, которые необходимо изучить
        :param init: Если параметр установлен, то удаляет предыдущий словарь и инициализирует новый. Если нет,
        то обучает старый словарь
        :return: None
        """
        if isinstance(learning_content, tuple):
            learning_content = [learning_content]

        # word - ключ, value[0] - всего, value[1] - появлений в spam, value[2] - появлений в ham
        dictionary = defaultdict(lambda: [0, 0, 0])

        # TODO parse in parallel
        for index, (msg, spam) in enumerate(learning_content):
            logger.info('Proccess message N: %d' % index)
            value_list_index = 1 if spam else 2
            words = set(ContentParser.parse(msg).split(' ')) if msg else {}

            for word in words:
                if word:
                    dictionary[word][0] += 1
                    dictionary[word][value_list_index] += 1

        dict_counter = Counter()

        for k, v in dictionary.items():
            dict_counter[k] = v[0]

        updates = [{
            'word': item[0],
            'spam_count': dictionary[item[0]][1],
            'ham_count': dictionary[item[0]][2]
        } for item in dict_counter.most_common(learn_words_num)]

        def on_commit(items, init_flag):
            if init_flag:
                invalidate_model(Dictionary)
            else:
                # у запроса aggregate также сбросится кэш при сбрасывании кэша одной записи
                for instance in items:
                    invalidate_obj(instance)

        if updates:
            with transaction.atomic():
                if init:
                    cls.objects.all().delete()
                    update_words = None
                else:
                    update_words = list(cls.objects.filter(word__in=[item['word'] for item in updates])
                                        .select_for_update())

                cls.objects.bulk_update_or_create(updates, key_fields='word',
                                                  set_functions={'spam_count': '+', 'ham_count': '+'})
                transaction.on_commit(lambda: on_commit(update_words, init))

    @classmethod
    def check_message_for_spam(cls, message: str) -> bool:
        """
        Проверяет сообщение на спам
        :param message: Сообщение, которое проверяется на спам
        :return: boolean. Спам или нет
        """
        parse_content = ContentParser.parse(message) if message else ''
        words = {item for item in parse_content.split(' ')}

        # все запросы к Dictionary кэшируются на сутки или до нового обучения словаря.
        aggr_sum = cls.objects.aggregate(sum_spam=Sum('spam_count'), sum_ham=Sum('ham_count'))
        qs = cls.objects.filter(word__in=words).values_list('word', 'spam_count', 'ham_count')
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
        return spam_probability > 0.9

    @classmethod
    def check_dictionary_for_valid(cls, spam_file_path: str, ham_file_path: str, delimiter: str,
                                   num_msg_to_check: int = 100) -> List[Tuple[str, bool]]:
        """
        Проверяет получившийся словарь на валидность и возвращает список сообщений, которые неправильно идентифицированы
        как спам или наоборот - не спам идентифицирован как спам
        :param spam_file_path: Путь до файла со спамом
        :param ham_file_path: Путь до файла с сообщениями без спама
        :param delimiter: разделитель
        :param num_msg_to_check: Число сообщений попадающих в выборку
        :return:
        """
        errors = []

        def _get_content_from_file(filename: str):
            with open(filename, 'r') as f:
                return f.read().split(delimiter)

        def _check_for_errors(content: List[str], spam: bool):
            for index, msg in enumerate(content):
                logger.info('Proccess record: %d in %s spam dictionary' % (index, spam))

                if spam != cls.check_message_for_spam(msg):
                    errors.append((msg, spam))

        # Письма, которых не было в обучении
        spam_content = _get_content_from_file(spam_file_path)[:num_msg_to_check]
        ham_content = _get_content_from_file(ham_file_path)[:num_msg_to_check]

        _check_for_errors(spam_content, True)
        _check_for_errors(ham_content, False)

        return errors
