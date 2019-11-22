from django.core.exceptions import ValidationError
from django.db.models import Manager, QuerySet


class NNQuerySet(QuerySet):
    """
    Manager модели нейросети, непозволяющий создавать более одной записи в БД.
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


NNManager = Manager.from_queryset(NNQuerySet)()
