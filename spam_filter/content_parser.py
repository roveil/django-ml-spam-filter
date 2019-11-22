import re
from itertools import chain, product
from typing import List, Tuple, Union

import emoji
from html.parser import HTMLParser as BaseHTMLParser
from nltk import pos_tag, word_tokenize
from nltk.corpus import wordnet, words
from nltk.stem import WordNetLemmatizer, SnowballStemmer
from pymorphy2 import MorphAnalyzer

# Поиск линейный по words.words() со всеми вытекающими. В памяти занимает 8 мб, решил не заморачиваться с БД
english_words = set(words.words())


class HTMLParser(BaseHTMLParser):

    def error(self, message):
        pass

    def __init__(self):
        super().__init__()
        self._parse_data = []

    def handle_starttag(self, tag: str, _):
        if tag in {'a', 'img'}:
            self._parse_data.append('html_external_spec')

    def handle_data(self, data: str) -> None:
        tag_string = self.get_starttag_text() or ''

        m = re.search(r'(<style)|(<head)|(<script)|(<meta)|(<img)|(<title)', tag_string, re.I)
        m2 = re.match(r'.*[A-z\-]+\s*:.*;.*}', data, re.DOTALL)

        if not m and (tag_string or (not tag_string and not m2)):
            self._parse_data.append(data)

    def get_clear_data(self, content: str) -> str:
        self.feed(content)
        return ' '.join(self._parse_data)


class ContentParser:
    special_words = {'html_external_spec', 'email_spec', 'url_spec', 'dollar_spec', 'ruble_spec', 'phone_spec',
                     'number_spec', 'percent_spec'}

    # Если встречается слово из values заменяем на ключ
    # pymorphy(рус. распознаватель) распознает месяц несмотря на регистр первой буквы
    # january в словаре words.words() нет, а January есть.
    # Решил не костылять и оставить, что месяц с маленькой буквы попадет в словарь unknown_words
    words_replaces = {
        'месяц': {'январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль', 'август', 'сентябрь', 'ноябрь',
                  'декабрь'},
        'month': {'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                  'November', 'December'}
    }

    @staticmethod
    def get_stripped_html(body: str) -> str:
        """
        Получает строку, очищенную от html-содержимого
        :param body: содержимое
        :return: содержимое, очищенное от html
        """
        parser = HTMLParser()
        return parser.get_clear_data(body)

    @staticmethod
    def get_emojies(body: str) -> List[str]:
        """
        Находит emoji в контенте
        :param body: контент
        :return: Список с emoji
        """
        return [char for char in body if char in emoji.UNICODE_EMOJI]

    @staticmethod
    def replace_special_char(body: str) -> str:
        """
        Заменяет ссылки (в том числе в html тегах) на 'urladdr', емейл-адреса на 'emailaddr', отдельно стоящий знак
        $ на 'dollar'. Убираем табуляцию переносы строк и пробелы
        :param body: контент
        :return: очищенный по различным регулярным выражениям контент
        """
        regexp_exchange = [
            (r'_+', '_'),
            (r"[A-z0-9.!#$%&'*+-/=?^_`{|}~@]+@[A-z0-9-\.:]+", ' email_spec '),
            (r"((\d+|\s)\$)", ' dollar_spec '),
            (r'(https?)?(:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.'
             r'[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)', ' url_spec '),
            (r"((\d+|\s)₽)", ' ruble_spec '),
            (r'\(|\)|\!|\.|\?|:|\\|/|\[|\]', ''),
            (r'(((\+\d+)|(8))[\s-]?\d+[\s-]\d+[\s-]\d+[\s-]?\d+)|(((\+\d+)|(8))\d{10})', ' phone_spec '),
            (r"\{(\{|%)\s?.+\s?(\}|%)\}", ' '),  # убираем jinja2 подстановки
            (r'&[A-z0-9\#]{2,8};', ' '),  # убираем html - символы &nbsp; и прочие
            (r'"|«|»|\,|\-|“|”|\*|\||\'|;|{|}', ' '),
            (r'\d+', ' number_spec '),
            (r'\t', ' '),
            (r'(\r\n)|\n', ' '),
            (r'[\s\-]{1,}', ' '),  # заменяем любые пробелы на один пробел. \s включает в себя в том числе \xa0
            (r'([\d\-]+%)|%', 'percent_spec'),
            (r'[^\s]{255,}', '')  # удаляем все длиннее 255 символов, потому что я не знаю таких длинных слов
        ]

        for regexp, exchange in regexp_exchange:
            body = re.sub(regexp, exchange, body)

        return body.strip()

    @classmethod
    def _get_en_word_type(cls, word_type_tag: str) -> wordnet:
        """
        Возвращает специальный объект wordnet. Необходим для определения части речи (Существительное, прилагательное..)
        в английском языке.
        :param word_type_tag: строка
        :return: Объект wordnet
        """
        if word_type_tag.startswith('J'):
            return wordnet.ADJ
        elif word_type_tag.startswith('V'):
            return wordnet.VERB
        elif word_type_tag.startswith('N'):
            return wordnet.NOUN
        elif word_type_tag.startswith('R'):
            return wordnet.ADV
        else:
            return wordnet.NOUN

    @classmethod
    def analyze_words(cls, body: str) -> Tuple:
        """
        Опознает русские и английские слова и оставляет только их наиболее значимую часть
        :param body: контент
        :return: список неопознанных слов и содержимое после обработки слов
        """
        rus_lemm_analyzer = MorphAnalyzer()
        en_lemm_analyzer = WordNetLemmatizer()
        rus_stemmer = SnowballStemmer('russian')
        en_stemmer = SnowballStemmer('english')

        unknown_words = []
        rus_words = []
        en_words = []

        for word in re.findall(r'[А-я]{2,}', body):
            analysis = rus_lemm_analyzer.parse(word)[0]

            if analysis.is_known:
                rus_words.append(analysis.normal_form)
            else:
                unknown_words.append(analysis.normal_form)
                rus_words.append(analysis.normal_form)

        # для английских слов немного сложнее
        word_word_type = pos_tag(word_tokenize(' '.join(re.findall(r'[A-z]{2,}', body))))

        for sw in word_word_type:
            word = en_lemm_analyzer.lemmatize(sw[0], cls._get_en_word_type(sw[1]))

            if word not in cls.special_words and word not in english_words:
                unknown_words.append(word)
            en_words.append(word)

        result = []

        for lang, item in chain(product(['ru'], rus_words), product(['en'], en_words)):
            stemmer = rus_stemmer if lang == 'ru' else en_stemmer

            for k, v in cls.words_replaces.items():
                if item in v:
                    result.append(stemmer.stem(k))
                    break
            else:
                result.append(stemmer.stem(item))

        return unknown_words, ' '.join(result)

    @staticmethod
    def get_uppercase_words(body: str) -> List[str]:
        """
        Возвращает все слова в верхнем регистре из содержимого body
        :param body: контент
        :return: список слов в верхнем регистре
        """
        return re.findall(r'[A-ZА-Я]{2,}', body)

    @staticmethod
    def get_num_html_colors(body: str) -> int:
        """
        Получить количество цветов css из html содержимого
        :param body: содержимое
        :return: количество цветов в документе
        """
        return len(re.findall(r'color\s*:\s*(([A-Za-z]+)|(#[A-Fa-f0-9]+)|)', body))

    @classmethod
    def parse(cls, body: str, identify_words: bool = True) -> str:
        """
        Распознает значимые слова из сообщения
        :param body: тело сообщения
        :param identify_words: Распознавать русские слова и приводить их в нормальную форму и к нижнему регистру
        :return: строку с распознанными словами в сообщении разделенные через пробел
        """
        body = cls.get_stripped_html(body)
        body = cls.replace_special_char(body)

        if identify_words:
            _, body = cls.analyze_words(body)

        return body

    @classmethod
    def prepare_for_pnn(cls, body: str) -> Union[bool, Tuple[str, Tuple[float, float, float, int, int, float]]]:
        """
        Подготавливает информацию о содержимом для pnn
        :param body: содержимое
        :return: распаршенное содержимое сообщения, частота слов верхнего регистра, частота чисел, число css цветов,
        размер полезного контента в байтах, сли есть полезная информация иначе False
        """
        # не определяю слова сразу, т.к. необходимо узнать количество слов в верхнем регистре.
        parsed_body = cls.parse(body, identify_words=False)

        if parsed_body:
            unknown_words, parsed_words_body = cls.analyze_words(parsed_body)
            num_words = len(parsed_words_body.split(' '))

            uppercase_freq = len(cls.get_uppercase_words(parsed_body)) / num_words
            num_freq = len(re.findall('number_spec', parsed_words_body)) / num_words
            content_size = len(parsed_words_body) * 2 / 1024  # UTF-8 содержит в себе 2 байта. Размер в кб
            num_colors = cls.get_num_html_colors(body)
            num_emojies = len(cls.get_emojies(parsed_body))
            unknown_freq = len(unknown_words) / num_words

            return parsed_words_body, (uppercase_freq, num_freq, content_size, num_colors, num_emojies, unknown_freq)
        else:
            return False
