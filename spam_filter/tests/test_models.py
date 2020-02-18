from django.db import IntegrityError
from django.test.testcases import TestCase

from django_ml_spam_filter.utils import exec_in_parallel
from spam_filter.models import NNStructure


class SingleRowTableTest(TestCase):

    def test_single_row_table_concurrency(self, proc_num: int = 10):
        def _create(*_):
            try:
                NNStructure.objects.create(weights=b'test')
            except IntegrityError:
                pass

        args = [((i,), {}) for i in range(proc_num)]
        exec_in_parallel(_create, args, processes_count=proc_num, need_db_refresh=True)

        self.assertEqual(1, NNStructure.objects.nocache().count())
