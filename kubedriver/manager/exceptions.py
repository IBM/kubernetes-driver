
## Persistence Errors
class PersistenceError(Exception):
    pass

class InvalidUpdateError(PersistenceError):
    pass

class RecordNotFoundError(PersistenceError):
    pass

## Manager Errors
class RequestInvalidStateError(Exception):
    pass