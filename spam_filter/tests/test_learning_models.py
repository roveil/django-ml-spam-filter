from django.db.models import Sum
from django.test import TestCase, TransactionTestCase

from spam_filter.learning_models import BayesModel, NN
from spam_filter.mail_source import FileMailContentSource


class BayesModelTest(TestCase):
    def setUp(self):
        self.spam = FileMailContentSource('spam_filter/tests/html_templates/template_1.html', '**********\n')
        self.ham = FileMailContentSource('spam_filter/tests/html_templates/template_2.html', '**********\n')

    def _check_for_spam(self, content, predicted_res):
        check_res = BayesModel.check_message_for_spam(content)
        self.assertEqual(predicted_res, check_res)

    def test_train(self):
        BayesModel.train(spam=self.spam, ham=self.ham, init=True)
        self._check_for_spam(self.spam.get_content()[0], True)
        self._check_for_spam(self.ham.get_content()[0], False)
        aggr = BayesModel.db_model.objects.aggregate(sum_spam=Sum('spam_count'), sum_ham=Sum('ham_count'))

        # Дотренировываем модель
        BayesModel.train(spam=self.spam, ham=self.ham)
        self._check_for_spam(self.spam.get_content()[0], True)
        self._check_for_spam(self.ham.get_content()[0], False)
        new_aggr = BayesModel.db_model.objects.aggregate(sum_spam=Sum('spam_count'), sum_ham=Sum('ham_count'))
        self.assertEqual(2 * aggr['sum_spam'], new_aggr['sum_spam'])
        self.assertEqual(2 * aggr['sum_ham'], new_aggr['sum_ham'])

    def test_train_min_word_appearance(self):
        BayesModel.train(spam=self.spam, ham=self.ham, init=True, min_num_word_appearance=2)
        exists = BayesModel.db_model.objects.filter(word__contains='subscrib').exists()
        self.assertTrue(exists)

        exists = BayesModel.db_model.objects.exclude(word__contains='subscrib').exists()
        self.assertFalse(exists)


class NNModelTest(TransactionTestCase):
    def setUp(self):
        self.spam = FileMailContentSource('spam_filter/tests/html_templates/template_1.html', '**********\n')
        self.ham = FileMailContentSource('spam_filter/tests/html_templates/template_2.html', '**********\n')
        BayesModel.train(spam=self.spam, ham=self.ham, init=True)

    def _check_for_spam(self, content, predicted_res):
        check_res = NN.check_message_for_spam(content)
        self.assertEqual(predicted_res, check_res)

    def test_train(self):
        # Сеть большая. Необходимо много данных для обучения и повторений, чтобы каждый нейрон обновил вес
        learning_content = [(self.spam.get_content()[0], True) for _ in range(250)]
        learning_content.extend([(self.ham.get_content()[0], False) for _ in range(250)])
        NN.train(learning_content=learning_content, init=True)

        self._check_for_spam(self.spam.get_content()[0], True)
        self._check_for_spam(self.ham.get_content()[0], False)

        # Дотренировываем модель
        NN.train(learning_content=learning_content)
        self._check_for_spam(self.spam.get_content()[0], True)
        self._check_for_spam(self.ham.get_content()[0], False)
