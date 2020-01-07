from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django_pg_bulk_update.manager import BulkUpdateManager
from django_pg_returning import UpdateReturningMixin


class NNQuerySet(QuerySet):
    """
    Queryset модели нейросети, непозволяющий создавать более одной записи в БД.
    В таблице мы храним одну строку с весами нейросети
    """

    def create(self, **kwargs):
        if not self.exists():
            return super().create(**kwargs)
        else:
            raise ValidationError('This model is for one entry only')

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False):
        if not self.exists() and len(objs) == 1:
            return super().bulk_create(objs, batch_size=batch_size, ignore_conflicts=ignore_conflicts)
        else:
            raise ValidationError('This model is for one entry only')

    def get(self, *args, **kwargs):
        return super().get()


class NNManager(UpdateReturningMixin, BulkUpdateManager):
    def get_queryset(self):
        return NNQuerySet(using=self.db, model=self.model)


class BayesDictonaryManager(UpdateReturningMixin, BulkUpdateManager):
    pass
