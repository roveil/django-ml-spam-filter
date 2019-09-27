import hashlib
import hmac

from django.conf import settings


def get_signature(msg: str):
    return hmac.new(key=settings.SECURE_TOKEN.encode(), msg=msg.encode(), digestmod=hashlib.sha256).hexdigest()
