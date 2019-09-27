import emoji
import pymorphy2
import re

from html.parser import HTMLParser as BaseHTMLParser


class HTMLParser(BaseHTMLParser):

    def __init__(self):
        super().__init__()
        self.parse_data = []

    def handle_starttag(self, tag, attrs):
        if tag in {'a', 'img'}:
            self.parse_data.append('html_external_content')

    def handle_data(self, data: str) -> None:
        tag_string = self.get_starttag_text() or ''

        m = re.search(r'(<style)|(<head)|(<script)|(<meta)|(<img)', tag_string, re.I)

        if not m:
            self.parse_data.append(data)

    def get_clear_data(self, content: str, delimiter: str) -> str:
        self.feed(content)
        return delimiter.join(self.parse_data)


class ContentParser:
    rus_months = {'январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль', 'август', 'сентябрь', 'ноябрь',
                  'декабрь'}

    @classmethod
    def get_html_stripped_content(cls, body: str, delimiter: str = ' ') -> str:
        """
        Получает строку, очищенную от html-содержимого
        :param body: содержимое
        :param delimiter: разделитель между словами
        :return: содержимое, очищенное от html
        """
        parser = HTMLParser()
        return parser.get_clear_data(body, delimiter)

    @classmethod
    def identify_emoji(cls, body: str, delimiter: str = ' ') -> str:
        """
        Находит emoji в контенте и отделяет их в отдельное слово.
        :param body: контент
        :param delimiter: разделитель между словами
        :return: контент с emoji.
        """
        result = []
        emojies = []

        for word in body.split(delimiter):
            clean_word = []

            for c in word:
                if c in emoji.UNICODE_EMOJI:
                    emojies.append(c)
                else:
                    clean_word.append(c)

            if clean_word:
                result.append(''.join(clean_word))

        result.extend(emojies)

        return delimiter.join(result)

    @classmethod
    def replace_special_content(cls, body: str) -> str:
        """
        Заменяет ссылки (в том числе в html тегах) на 'urladdr', емейл-адреса на 'emailaddr', отдельно стоящий знак
        $ на 'dollar'. Убираем табуляцию переносы строк и пробелы
        :param body: контент
        :return: очищенный по различным регулярным выражениям контент
        """
        regexp_exchange = [
            (r"[A-z0-9.!#$%&'*+-/=?^_`{|}~@]+@[A-z0-9-\.:]+", ' emailaddr '),
            (r"((\d+|\s)\$)", ' dollar '),
            (r'(https?)?(:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.'
             r'[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)', ' urladdr '),
            (r"((\d+|\s)₽)", ' ruble '),
            (r'\(|\)|\!|\.|\?|:|\\|/|\[|\]', ''),
            (r'(((\+\d+)|(8))[\s-]?\d+[\s-]\d+[\s-]\d+[\s-]?\d+)|(((\+\d+)|(8))\d{10})', ' phone_number '),
            (r"\{(\{|%)\s?.+\s?(\}|%)\}", ' '),  # убираем jinja2 подстановки
            (r'&[A-z0-9\#]{2,8};', ' '),  # убираем html - символы &nbsp; и прочие
            (r'"|«|»|\,|\-|“|”|\*|\||\'|;|{|}', ' '),
            (r'\d+', ' single_number '),
            (r'\t', ' '),
            (r'(\r\n)|\n', ' '),
            (r'[\s\-]{1,}', ' '),  # заменяем любые пробелы на один пробел. \s включает в себя в том числе \xa0
            (r'([\d\-]+%)|%', 'percent_symbol'),
            (r'[^\s]{255,}', '')  # удаляем все длиннее 255 символов, потому что я не знаю таких длинных слов
        ]

        for regexp, exchange in regexp_exchange:
            body = re.sub(regexp, exchange, body)

        return body.strip()

    @classmethod
    def identify_russian_alphabet(cls, body: str, delimiter: str = ' '):
        """
        Опознает русские слова и приводит их в нормальную форму
        :param body: контент
        :param delimiter: разделитель между словами
        :return: контент после определения русских слов
        """
        parser = pymorphy2.MorphAnalyzer()
        result = []

        for item in body.split(delimiter):
            parse_result = parser.parse(item)[0].normal_form
            result.append(parse_result if parse_result not in cls.rus_months else 'date_month')

        return delimiter.join(result)

    @classmethod
    def parse(cls, body: str) -> str:
        """
        Распознает значимые слова из сообщения
        :param body: тело сообщения
        :return: строку с распознанными словами в сообщении разделенные через пробел
        """
        body = cls.get_html_stripped_content(body)
        body = cls.replace_special_content(body)
        body = body.lower()
        body = cls.identify_emoji(body)
        body = cls.identify_russian_alphabet(body)

        return body
