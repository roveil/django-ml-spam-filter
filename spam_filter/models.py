from django.db import models

from spam_filter.manager import NNManager, BayesDictonaryManager


class LearningMessage(models.Model):
    message = models.TextField()
    spam = models.BooleanField()
    processed = models.DateTimeField(null=True, blank=True)


class BayesDictionary(models.Model):
    word = models.CharField(max_length=255, db_index=True, unique=True)
    spam_count = models.PositiveIntegerField(default=0)
    ham_count = models.PositiveIntegerField(default=0)

    objects = BayesDictonaryManager()


class NNStructure(models.Model):
    weights = models.BinaryField()

    objects = NNManager()
