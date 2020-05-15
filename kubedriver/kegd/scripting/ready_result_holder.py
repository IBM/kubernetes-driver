
#Duplicates of ReadyResult constants - keeps this class clean of imported modules leaking into the sandbox
NOT_READY = 'NotReady'
READY = 'Ready'
FAILED = 'Failed'

class ReadyResultHolder:

    def __init__(self):
        self.__readiness = READY
        self.__reason = None

    def ready(self):
        self.__readiness = READY
        return self

    def not_ready(self):
        self.__readiness = NOT_READY
        return self

    def notReady(self):
        return self.not_ready()

    def failed(self, reason):
        self.__readiness = FAILED
        self.__reason = str(reason)
        return self

    def is_ready(self):
        return self.__readiness == READY

    def has_failed(self):
        return (self.__readiness == FAILED), self.__reason

    def __str__(self):
        return f'{self.__class__.__name__}(readiness: {self.__readiness}, reason: {self.__reason})'

    def __repr__(self):
        return f'{self.__class__.__name__}(readiness: {self.__readiness!r}, reason: {self.__reason!r}'


    