from .object_states import ObjectStates

class ObjectRecord:

    CONFIG = 'config'
    STATE = 'state'
    ERROR = 'error'

    def __init__(self, config, state=ObjectStates.PENDING, error=None):
        self.config = config
        self.state = state
        self.error = error

    @staticmethod
    def from_storage_data(self, data):
        config = data.get(ObjectRecord.CONFIG)
        state = data.get(ObjectRecord.STATE, ObjectStates.PENDING)
        error = data.get(ObjectRecord.ERROR, None)
        return ObjectRecord(config, state=state, error=error)

    def to_storage_data(self):
        data = {
            ObjectRecord.CONFIG: self.config,
            ObjectRecord.STATE: self.state,
            ObjectRecord.ERROR: self.error
        }
        return data

    def __str__(self):
        return f'{self.__class__.__name__}(config: {self.config}, state: {self.state}, error: {self.error})'

    def __repr__(self):
        return f'{self.__class__.__name__}(config: {self.config!r}, state: {self.state!r}, error: {self.error!r})'
