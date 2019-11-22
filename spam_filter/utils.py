import hashlib
import hmac

from django.conf import settings


def get_signature(msg: str):
    return hmac.new(key=settings.SECURE_TOKEN.encode(), msg=msg.encode(), digestmod=hashlib.sha256).hexdigest()


def get_content_from_file(filename: str, delimiter: str, max_items: int = 0):
    with open(filename, 'r') as f:
        result = f.read().split(delimiter)

        return result if not max_items else result[:max_items]
