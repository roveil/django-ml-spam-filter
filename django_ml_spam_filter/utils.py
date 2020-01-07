from typing import Callable, Optional, List, Any, Iterable, Tuple

from django.conf import settings
from django.db import connections
from multiprocessing import Process, Manager

from rest_framework.views import exception_handler as base_exception_handler


def rest_framework_exception_handler(ex: Exception, context: dict):
    response = base_exception_handler(ex, context)

    if response:
        response.data = {
            'meta': {
                'error': ex.__class__.__name__,
                'error_message': getattr(ex, 'detail', ''),
                'status': response.status_code
            },
            'data': {}
        }

    return response


class DBProcess(Process):
    """
    Закрывает соединениие к БД во время завершения процесса.
    """

    def __init__(self, need_db_refresh: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.need_db_refresh = need_db_refresh

    def run(self):
        if self.need_db_refresh:
            # переустанавливает соединение к БД в процессе. Иначе получим ошибку SSL Bad record mac
            for alias in connections:
                connections[alias].connect()

        super().run()


def exec_in_parallel(func: Callable, func_args: Iterable[Tuple[tuple, dict]] = None,
                     processes_count: Optional[int] = settings.NUM_CPU_CORES, need_db_refresh: Optional[bool] = False) \
        -> List[Any]:
    """
    Выполняет функцию func в несколько потоков параллельно.
    Предполагается, что функции независимы. Если необходимы блокировки, func должна сама их обеспечить.
    :param func: Функция для выполнения
    :param func_args: Iterable[((args), {kwargs})]
    :param processes_count: Количество потоков, которые могут быть запущены параллельно
    :param need_db_refresh: Если внутри func делаются запросы к БД, то необходимо обновить соединения внутри процессов
    :return: Список результатов. Порядок не гарантируется. Тип элементов зависит от func
    """
    manager = Manager()
    args_queue = manager.Queue()
    results_queue = manager.Queue()

    for args, kwargs in func_args:
        args_queue.put((args, kwargs))

    def _worker(arg_q, res_q, worker_func):
        while not args_queue.empty():
            args, kwargs = arg_q.get()
            local_res = worker_func(*args, **kwargs)
            res_q.put(local_res)
            arg_q.task_done()

    processes = [DBProcess(target=_worker, args=(args_queue, results_queue, func), need_db_refresh=need_db_refresh)
                 for _ in range(processes_count)]

    # Ждем окончания процесса
    for proc in processes:
        proc.start()

    for proc in processes:
        proc.join()

    results = []

    while not results_queue.empty():
        results.append(results_queue.get())

    return results
