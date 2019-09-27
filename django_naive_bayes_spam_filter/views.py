from django_naive_bayes_spam_filter.exceptions import Error404, Error500
from django_naive_bayes_spam_filter.responses import APIResponse


def handler404(request, _):
    return APIResponse(exception=Error404(request.path))


def handler500(request):
    return APIResponse(exception=Error500())
