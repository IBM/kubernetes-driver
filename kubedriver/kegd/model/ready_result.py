

class ReadyResult:

    NOT_READY = 'NotReady'
    READY = 'Ready'
    FAILED = 'Failed'

    @staticmethod
    def ready():
        return ReadyResult(ReadyResult.READY)

    @staticmethod
    def not_ready():
        return ReadyResult(ReadyResult.NOT_READY)

    @staticmethod
    def failed(reason):
        return ReadyResult(ReadyResult.FAILED, reason=reason)

    def __init__(self, readiness_state, reason=None):
        self.__readiness = readiness_state
        self.reason = reason

    def is_ready(self):
        return self.__readiness == ReadyResult.READY

    def has_failed(self):
        return (self.__readiness == ReadyResult.FAILED), self.reason

    def __str__(self):
        return f'{self.__class__.__name__}(readiness: {self.__readiness}, reason: {self.reason})'

    def __repr__(self):
        return f'{self.__class__.__name__}(readiness: {self.__readiness!r}, reason: {self.reason!r}'


