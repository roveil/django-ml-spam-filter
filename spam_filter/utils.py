import hashlib
import hmac

from django.conf import settings


def get_signature(msg: str):
    return hmac.new(key=settings.SECURE_TOKEN.encode(), msg=msg.encode(), digestmod=hashlib.sha256).hexdigest()


def get_content_from_file(filename: str, delimiter: str):
    with open(filename, 'r') as f:
        return f.read().split(delimiter)