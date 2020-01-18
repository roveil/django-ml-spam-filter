from django.test import TransactionTestCase, override_settings

from spam_filter.learning_models import BayesModel, NN
from spam_filter.models import LearningMessage
from spam_filter.tasks import process_auto_learning


class ProcessAutoLearningTest(TransactionTestCase):
    fixtures = ['spam_filter_learning_message']

    @override_settings(AUTO_LEARNING_ENABLED=True)
    def test_process_auto_learning(self):
        process_auto_learning()
        unprocessed = LearningMessage.objects.filter(processed__isnull=True).exists()
        self.assertFalse(unprocessed)

        spam_count = BayesModel.db_model.objects.filter(word="spam", spam_count=1, ham_count=0).count()
        self.assertEqual(1, spam_count)

        ham_count = BayesModel.db_model.objects.filter(word="ham", spam_count=0, ham_count=1).count()
        self.assertEqual(1, ham_count)

        weights_count = NN.db_model.objects.count()
        self.assertEqual(1, weights_count)
