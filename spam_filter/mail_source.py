from abc import ABC, abstractmethod
from typing import Iterable as TIterable, Optional, List

from perceval.backends.core.mbox import MBox

from spam_filter.utils import get_content_from_file


class MailContentSource(ABC):

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def get_content(self, max_items: Optional[int] = None) -> TIterable[str]:
        pass


class MBOXMailContentSource(MailContentSource):

    def __init__(self, mbox_path: str):
        """
        :param mbox_path: Путь до папки с MBOX письмами
        """
        self.mbox_path = mbox_path
        super().__init__()

    def get_content(self, max_items: Optional[int] = None) -> List[str]:
        """
        Получает только содержимое писем в MBOX хранилище писем игнорируя все заголовки
        :param max_items: Максимальное количество сообщений
        :return: генератор с содержимым писем архива MBOX
        """
        repo = MBox(self.mbox_path, self.mbox_path)
        result = []

        for index, msg in enumerate(repo.fetch()):
            if max_items and index >= max_items:
                break

            result.append(msg['data']['body'].get('html', msg['data']['body'].get('plain', '')))

        return result


class FileMailContentSource(MailContentSource):

    def __init__(self, filepath: str, delimiter: str):
        """
        :param filepath: Путь до файла с письмами
        :param delimiter: Разделитель между содержимым внутри файла
        """
        self.filepath = filepath
        self.delimiter = delimiter
        super().__init__()

    def get_content(self, max_items: Optional[int] = None) -> List[str]:
        """
        <p>Какой прекрасный день</p>
        **********
        <p>Сколько человек будут проживать?</p>
        **********
        Разделитель в данном случае - **********\n
        :param max_items: Максимальное количество сообщений
        :return: список из содержимого сообщений в файле
        """
        return get_content_from_file(self.filepath, self.delimiter, max_items=max_items)
