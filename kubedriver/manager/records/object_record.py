from .object_states import ObjectStates

class ObjectRecord:

    CONFIG = 'config'
    STATE = 'state'
    ERROR = 'error'

    def __init__(self, config, state=ObjectStates.PENDING, error=None):
        self.config = config
        self.state = state
        self.error = error

    def __str__(self):
        return f'{self.__class__.__name__}(config: {self.config}, state: {self.state}, error: {self.error})'

    def __repr__(self):
        return f'{self.__class__.__name__}(config: {self.config!r}, state: {self.state!r}, error: {self.error!r})'
