# Django naive bayes spam filter
* Спам фильтр построенный по наивной Байесовской теории фильтрации спама.
Ссылка на теорию: http://ceur-ws.org/Vol-837/paper18.pdf
* REST API позволяет обучать фильтр, проверять контент на спам.
* Флаг AUTO_LEARNING_ENABLED = True позволяет автоматически учиться на проверенном сообщении.

## Установка

* Установить виртуальное окружение

* Установить зависимости виртуального окружения:

  ```shell
  pip install -Ur requirements.txt
  ```
* Создать файл `config.py` и отредактировать его по примеру config.dist.py

* Запуск celery и gunicorn:

  ```ini
  Запуск celery-worker
  .../bin/celery -A django_naive_bayes_spam_filter worker -l INFO -c 4  -Q spam_filter_main -n worker-net.%%h -Ofair

  Запуск celery-beat
  .../bin/celery -A django_naive_bayes_spam_filter beat -l INFO

  Запуск gunicorn
  gunicorn django_naive_bayes_spam_filter.wsgi:application --bind :8010 --workers 2
  ```




