from django.test import TestCase

from spam_filter.content_parser import ContentParser


class ContentParserTest(TestCase):

    def test_get_stripped_html(self):
        body = """<!DOCTYPE html><html lang="en"><p>test 123</p><a href="http://example.com">test link</a></html>"""
        content = ContentParser.get_stripped_html(body)
        self.assertEqual("test 123 html_external_spec test link", content)

    def test_get_emojies(self):
        body = """Первое предложение! 🤐 Второе предложение! 😞 Третье предложение. Какой хороший день 😀"""
        emojies = ContentParser.get_emojies(body)
        self.assertListEqual(['🤐', '😞', '😀'], emojies)

    def test_replace_special_char(self):
        body = """телефон: 89001112233. email: test@example.com. супер предложение: 88 штук за 123 ₽ или 2$.
        экономия составит 50%.      немного отступа после предложения.  {% [jinja_2_content] %}
        """
        content = ContentParser.replace_special_char(body)
        predicted_content = "телефон phone_spec email email_spec супер предложение number_spec штук за number_spec " \
                            "ruble_spec или dollar_spec экономия составит number_spec percent_spec немного отступа " \
                            "после предложения"
        self.assertEqual(predicted_content, content)

    def test_analyze_words(self):
        """Проверим определение опознанных и неопознанных слов. Предугадать как алгоритмы будут выбирать значимую часть
        не имеет смысла.
        """
        body = "телефон алфванесуществующееслово фоывафываф существует слово. cat dog exist word flkdasjflasdf " \
               "html_external_spec number_spec ruble_spec dollar_spec ipohiksefdasf phone_spec url_spec"
        unknown_words, content = ContentParser.analyze_words(body)
        self.assertListEqual(['алфванесуществующеесловый', 'фоывафывафа', 'flkdasjflasdf', 'ipohiksefdasf'],
                             unknown_words)
        predicted_content = "телефон алфванесуществующееслов фоывафываф существова слов cat dog exist word " \
                            "flkdasjflasdf html_external_spec number_spec ruble_spec dollar_spec ipohiksefdasf " \
                            "phone_spec url_spec"
        self.assertEqual(predicted_content, content)

    def test_get_uppercase_words(self):
        body = "авыфавфыа СЛОВА В ВЕРХНЕМ РЕГИСТРЕ. АКЦИя ПРЕДЛОЖЕНИЯ скидки"
        upper_words = ContentParser.get_uppercase_words(body)

        self.assertListEqual(['СЛОВА', 'ВЕРХНЕМ', 'РЕГИСТРЕ', 'АКЦИ', 'ПРЕДЛОЖЕНИЯ'], upper_words)

    def test_colors(self):
        with open('spam_filter/tests/html_templates/template_1.html', 'r') as f:
            body = f.read()

        num_colors = ContentParser.get_num_html_colors(body)
        self.assertEqual(num_colors, 21)

    def test_parse(self):
        """
        Проверим что нет никаких артефактов на реальном html-документе. Все необходимые для распознавания подстановки
        произведены.
        """
        with open('spam_filter/tests/html_templates/template_1.html', 'r') as f:
            body = f.read()

        predicted_content = "html_external_spec html_external_spec html_external_spec home current " \
                            "html_external_spec portfolio html_external_spec blog entri html_external_spec contact " \
                            "us adult number_spec number_spec number_spec number_spec number_spec number_spec " \
                            "number_spec number_spec number_spec number_spec children number_spec number_spec " \
                            "number_spec number_spec number_spec number_spec number_spec number_spec number_spec " \
                            "number_spec number_spec room number_spec number_spec number_spec number_spec " \
                            "number_spec number_spec number_spec number_spec number_spec number_spec check avail " \
                            "lorem ipsum dolor sit amet consectetur adipisc elit html_external_spec need help we be " \
                            "here to help you subscrib to get our newslett html_external_spec subscrib newlett " \
                            "pellentesqu accumsan arcu nec dolor tempus pellentesqu at velit ant dui scelerisqu " \
                            "metus vel feli porttitor gravida donec at feli libero mauri odio tortor " \
                            "html_external_spec continu read dui scelerisqu metus vel feli porttitor pellentesqu " \
                            "at velit ant dui scelerisqu metus vel feli porttitor gravida donec at feli libero mauri " \
                            "odio tortor html_external_spec continu read etiam aliquam arcu at " \
                            "mauri consectetur pellentesqu at velit ant dui scelerisqu metus vel feli porttitor " \
                            "gravida donec at feli libero mauri odio tortor html_external_spec continu read " \
                            "html_external_spec nunc in feli aliquet metus luctus iaculi aliquam ac lacus volutpat " \
                            "dictum risus at scelerisqu nulla nullam sollicitudin at augu venenati eleifend nulla " \
                            "ligula ligula egesta sit amet viverra id iaculi sit amet ligula html_external_spec get " \
                            "more info html_external_spec sed cursus dictum nunc qui molesti pellentesqu qui duo sit " \
                            "amet purus scelerisqu eleifend sed ut ero morbi viverra blandit massa in varius sed nec " \
                            "ex eu ex tincidunt iaculi curabitur eget turpi gravida html_external_spec view detail " \
                            "html_external_spec eget diam pellentesqu interdum ut porta aenean finibus tempor nulla " \
                            "et maximus nibh dapibus ac dui consequat sed sapien venenati consequat aliquam ac lacus " \
                            "volutpat dictum risus at scelerisqu nulla html_external_spec more info " \
                            "html_external_spec lorem ipsum dolor sit amet consectetur suspendiss molesti sed dui " \
                            "eget faucibus dui accumsan sagitti tortor in ultric praesent tortor ant fringilla ac " \
                            "nibh porttitor fermentum commodo nulla html_external_spec detail info " \
                            "html_external_spec orci varius natoqu penatibus et pellentesqu qui duo sit amet purus " \
                            "scelerisqu eleifend sed ut ero morbi viverra blandit massa in varius sed nec ex eu ex " \
                            "tincidunt iaculi curabitur eget turpi gravida html_external_spec read more " \
                            "html_external_spec nullam sollicitudin at augu venenati eleifend aenean finibus tempor " \
                            "nulla et maximus nibh dapibus ac dui consequat sed sapien venenati consequat aliquam ac " \
                            "lacus volutpat dictum risus at scelerisqu nulla html_external_spec more detail " \
                            "recommend place enamel pin clich tild kitsch and vhs thundercat html_external_spec " \
                            "html_external_spec europ html_external_spec html_external_spec asia html_external_spec " \
                            "html_external_spec africa html_external_spec html_external_spec south america your " \
                            "browser do not support the video tag asia singapor html_external_spec suspendiss vel " \
                            "est libero sem phasellus ac laoreet integ libero purus consectetur vita posuer qui " \
                            "maximus id diam vivamus eget tellus ornar sollicitudin quam id dictum nulla phasellus " \
                            "finibus rhoncus justo tempus eleifend nequ dictum ac aenean metus leo consectetur non " \
                            "etiam aliquam arcu at mauri consectetur scelerisqu integ elementum justo in orci " \
                            "facilisi ultrici pellentesqu at velit ant dui scelerisqu metus vel feli porttitor " \
                            "gravida html_external_spec suspendiss vel est libero sem phasellus ac laoreet dui " \
                            "accumsan sagitti tortor in ultric praesent tortor ant fringilla ac nibh porttitor " \
                            "fermentum commodo nulla html_external_spec continu read html_external_spec faucibus " \
                            "dolor ligula nisl metus auctor aliquet nunc in feli aliquet metus luctus iaculi vel et " \
                            "nisi nulla venenati nisl orci laoreet ultrici massa tristiqu id html_external_spec " \
                            "continu read send messag now copyright number_spec your compani design tooplat"
        content = ContentParser.parse(body)
        self.assertEqual(predicted_content, content)
