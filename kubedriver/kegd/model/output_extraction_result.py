

class OutputExtractionResult:

    SUCCESS = 'Success'
    FAILED = 'Failed'

    @staticmethod
    def success(outputs=None):
        return OutputExtractionResult(OutputExtractionResult.SUCCESS, outputs=outputs)

    @staticmethod
    def failed(reason):
        return OutputExtractionResult(OutputExtractionResult.FAILED, reason=reason)

    def __init__(self, status, outputs=None, reason=None):
        self.status = status
        self.outputs = outputs if outputs is not None else {}
        self.reason = reason

    def is_ok(self):
        return self.status == OutputExtractionResult.SUCCESS

    def has_failed(self):
        return (self.status == OutputExtractionResult.FAILED), self.reason

    def __str__(self):
        return f'{self.__class__.__name__}(status: {self.status}, outputs: {self.outputs}, reason: {self.reason})'

    def __repr__(self):
        return f'{self.__class__.__name__}(status: {self.status!r}, outputs: {self.outputs!r}, reason: {self.reason!r}'
