# app/exceptions.py

from sanic.exceptions import SanicException
from sanic import response

class NotFound(SanicException):
    status_code = 404

class ServerError(SanicException):
    status_code = 500

def bad_request(request, exception):
    return response.json({'error': str(exception)}, status=exception.status_code)
