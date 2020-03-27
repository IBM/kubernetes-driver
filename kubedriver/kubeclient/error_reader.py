import json

class ErrorReader:

    def __load_body(self, error):
        try:
            body = json.loads(error.body)
            return True, body
        except Exception as e:
            pass
        return False, None

    def is_already_exists_err(self, error):
        body_valid, body = self.__load_body(error)
        return (body_valid and body.get('reason', None) == 'AlreadyExists' 
                and error.status == 409 
                and error.reason == 'Conflict')

    def is_not_found_err(self, error):
        body_valid, body = self.__load_body(error)
        return (body_valid and body.get('reason', None) == 'NotFound' 
                and error.status == 404 
                and error.reason == 'Not Found')
