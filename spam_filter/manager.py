from django.db.models import QuerySet
from django_pg_bulk_update.manager import BulkUpdateManager
from django_pg_returning import UpdateReturningMixin


class NNQuerySet(QuerySet):
    """
    Сделаем возможным получение весов нейросети при любых параметров
    Ограничение на создание в соответствубщем UNIQUE CONSTRAINT в БД.
    """

    def get(self, *args, **kwargs):
        return super().get()


class NNManager(UpdateReturningMixin, BulkUpdateManager):
    def get_queryset(self):
        return NNQuerySet(using=self.db, model=self.model)


class BayesDictonaryManager(UpdateReturningMixin, BulkUpdateManager):
    pass
