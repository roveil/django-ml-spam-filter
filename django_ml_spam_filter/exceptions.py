from rest_framework.exceptions import APIException


class Error500(APIException):
    code = 500
    message = "Internal server error"


class Error404(APIException):
    code = 404
    message = "Page not found"

    def __init__(self, url):
        self.message = "Path '%s' not found" % url
