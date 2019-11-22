# Spam Machine Learning Filter
#### В качестве моделей машинного обучения используется Байесовская классификация спама и многослойный персептрон.
* Неросеть принимает на вход параметры, в том числе результат Байесовской классификации и обучается классификации на спам
#### Классификация происходит исходя из параметров сообщения:
* Спам фильтр построенный по наивной Байесовской теории фильтрации спама.
Ссылка на теорию: http://ceur-ws.org/Vol-837/paper18.pdf
* Частота слов в верхнем регистре
* Частота появления чисел
* Размер сообщения
* Количество цветов
* Количество смайлов (emojies)
* Частота слов с неизвестным значением (поддерживаются русский, английский языки)
##### REST API позволяет обучать фильтр, проверять контент на спам.
##### Флаг AUTO_LEARNING_ENABLED = True позволяет автоматически учиться на проверенных сообщениях.

## Установка в docker-container
* Запустить скрипт install_as_container.py с параметром пути, куда положить файлы для сборки контейнера
  ```shell
  python install_as_container.py /path/to/container/workdir
  ```
* Если docker установлен, то исполнить скрипт /path/to/container/workdir/service.sh
  ```
  sudo /path/to/container/workdir/service.sh 
  ```
#### Настроика различных переменных происходит в .env, private/environment_common, build/config.container.py

#### Для того, чтобы обучить контейнер необходимо:
* Собрать контейнер, прокинув папку хоста в к контейнер: docker-compose.yml (service: app, секция volumes)
* Скопировать файлы для обучения (Директория с mbox файлами или файл с сообщениями) в расшаренную папку
* Произвести обучение исполнив в manage.py shell подобный код
  ```
  python manage.py shell
  from spam_filter.learning_models import *
  from spam_filter.mail_source import *
  spam = MBOXMailContentSource('/app/learning_content/mails')
  ham = FileMailContentSource('/app/learning_content/nonspambig.txt', '**********\n')
  NN.train(spam, ham, init=True, batch_size=5000)
  test = NN.check_for_valid(spam, ham)
  BayesModel.train(spam, ham, init=True, min_num_word_appearance=3)
  ```
