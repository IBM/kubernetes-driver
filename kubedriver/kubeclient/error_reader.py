import json

class ErrorReader:

    def __load_body(self, error):
        try:
            body = json.loads(error.body)
            return True, body
        except Exception as e:
            pass
        return False, None

    def is_client_error(self, error):
        return error.status >= 400 and error.status < 500

    def summarise_error(self, error):
        summary = f'ApiError ({error.status}, {error.reason})'
        body_valid, body = self.__load_body(error)
        if body_valid is True:
            body_msg = body.get('message')
            if body_msg is not None:
                summary += f' -> {body_msg}'
            body_reason = body.get('reason')
            if body_reason is not None:
                summary += f' -> {body_reason}'
        return summary

    def is_already_exists_err(self, error):
        body_valid, body = self.__load_body(error)
        return (body_valid and body.get('reason') == 'AlreadyExists' 
                and error.status == 409 
                and error.reason == 'Conflict')

    def is_not_found_err(self, error):
        body_valid, body = self.__load_body(error)
        return (body_valid and body.get('reason') == 'NotFound' 
                and error.status == 404 
                and error.reason == 'Not Found')
