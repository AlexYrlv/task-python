from sanic.response import json
from sanic.exceptions import SanicException

class NotFound(SanicException):
    status_code = 404

class ServerError(SanicException):
    status_code = 500

def bad_request(request, exception):
    return json({'error': str(exception)}, status=exception.status_code)

# Этот файл определяет исключения, которые могут возникать в приложении, и их обработчики.

# а кастомные исключения (NotFound и ServerError) помогают обрабатывать ошибки и возвращать корректные HTTP-ответы.