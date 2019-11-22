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
