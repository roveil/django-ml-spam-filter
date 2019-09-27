from rest_framework import permissions

from spam_filter.utils import get_signature


class AccessPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # У view класса должен быть атрибут signed field. Поле, хэш которого подписан SECURE_TOKEN
        signed_field = getattr(view, 'signed_field', '')

        return request.data.get('signature', '')[:64] == get_signature(str(request.data.get(signed_field)))
