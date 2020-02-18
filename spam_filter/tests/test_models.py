from multiprocessing.pool import ThreadPool as Pool
from django.db import DatabaseError
from django.test import TransactionTestCase

from spam_filter.models import NNStructure


class SingleRowTableTest(TransactionTestCase):

    def test_single_row_table_concurrency(self, proc_num: int = 10):
        def _create(*_):
            try:
                NNStructure.objects.create(weights=b'test')
            except DatabaseError:
                pass

        with Pool(proc_num) as pool:
            pool.map(_create, [i for i in range(proc_num)])
            pool.close()
            pool.join()

        self.assertEqual(1, NNStructure.objects.nocache().count())
