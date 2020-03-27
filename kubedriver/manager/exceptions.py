
## Persistence Errors
class PersistenceError(Exception):
    pass

class GroupRecordAlreadyExistsError(Exception):
    
    def __init__(self, group_uid, prefix=None):
        message = f'A record already exists for Group with ID \'{group_uid}\''
        if prefix != None:
            message = f'{prefix} {message}'
        super().__init__(message)
        self.group_uid = group_uid

class GroupRecordNotFoundError(Exception):

    def __init__(self, group_uid, prefix=None):
        message = f'A record for Group with ID \'{group_uid}\' could not be found'
        if prefix != None:
            message = f'{prefix} {message}'
        super().__init__(message)
        self.group_uid = group_uid

## Manager Errors
class RequestNotFoundError(Exception):
    pass

class RequestInvalidStateError(Exception):
    pass