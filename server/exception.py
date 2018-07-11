import json
from aiohttp.web_exceptions import HTTPException


class APIException(HTTPException):
    status_code = 400

    def __init__(self, *, status, message, content_type='application/json'):
        response_data = json.dumps({
            'error': {
                'error_code': status,
                'error_message': message
            }
        })
        HTTPException.__init__(self, text=response_data, content_type=content_type)


class InternalServerError(APIException):
    def __init__(self):
        APIException.__init__(self, status=1100, message='Internal server error.')


class MissingParameter(APIException):
    def __init__(self, param_name):
        APIException.__init__(self, status=1101, message='Missing parameter: %s.' % param_name)


class InvalidParameter(APIException):
    def __init__(self, param_name):
        APIException.__init__(self, status=1102, message='Invalid parameter: %s.' % param_name)


class InvalidAccessToken(APIException):
    def __init__(self):
        APIException.__init__(self, status=1103, message='Invalid access token.')
