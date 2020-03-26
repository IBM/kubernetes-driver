from .request_operations import RequestOperations
from .request_states import RequestStates

class RequestRecord:

    UID = 'uid'
    OPERATION = 'operation'
    STATE = 'state'
    ERROR = 'error'

    def __init__(self, uid, operation, state=RequestStates.PENDING, error=None):
        self.uid = uid
        self.operation = operation
        self.state = state
        self.error = error

    @staticmethod
    def from_storage_data(self, data):
        uid = data.get(RequestRecord.UID)
        request_type = data.get(RequestRecord.REQUEST_TYPE)
        state = data.get(RequestRecord.STATE, None)
        error = data.get(RequestRecord.ERROR, None)
        return RequestRecord(uid, request_type, state, error)

    def __str__(self):
        return f'{self.__class__.__name__}(uid: {self.uid}, operation: {self.operation}, state: {self.state}, error: {self.error})'

    def __repr__(self):
        return f'{self.__class__.__name__}(uid: {self.uid!r}, operation: {self.operation!r}, state: {self.state!r}, error: {self.error!r})'
