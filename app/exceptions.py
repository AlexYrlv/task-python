from sanic.response import json
from sanic.exceptions import SanicException

class NotFound(SanicException):
    status_code = 404

class ServerError(SanicException):
    status_code = 500

def bad_request(request, exception):
    return json({'error': str(exception)}, status=exception.status_code)
