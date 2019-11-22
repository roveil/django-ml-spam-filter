from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils.timezone import now
from statsd.defaults.django import statsd

from spam_filter.learning_models import BayesModel, NN
from spam_filter.models import LearningMessage


@statsd.timer('tasks.process_learning_message')
@shared_task(queue=settings.CELERY_QUEUE, ignore_result=True)
def process_learning_message():
    if settings.AUTO_LEARNING_ENABLED:
        with transaction.atomic():
            learning_content = LearningMessage.objects.filter(processed__isnull=True).select_for_update() \
                .values_list('message', 'spam')

            BayesModel.train(learning_content=learning_content)
            NN.train(learning_content=learning_content)
            learning_content.update(processed=now())
