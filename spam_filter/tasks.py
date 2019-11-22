from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils.timezone import now
from statsd.defaults.django import statsd

from spam_filter.models import BayesDictionary, LearningMessage


@shared_task(queue=settings.CELERY_QUEUE, ignore_result=True)
def process_learning_message():
    # TODO refactor
    pass
    # with statsd.timer('tasks.process_learning_message'):
    #     statsd.incr('tasks.process_learning_message')
    #
    #     with transaction.atomic():
    #         learning_content = LearningMessage.objects.filter(processed__isnull=True).select_for_update() \
    #             .values_list('message', 'spam')
    #
    #         learn_words_num = 4 * len(learning_content)  # Будем брать в среднем 4 самых популярных слова на сообщение
    #         BayesDictionary.train_dictionary(learning_content, learn_words_num=learn_words_num)
    #
    #         learning_content.update(processed=now())
