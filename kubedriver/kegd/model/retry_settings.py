

class RetrySettings:

    def __init__(self, max_attempts=None, timeout_seconds=None, interval_seconds=None):
        self.max_attempts = max_attempts
        self.timeout_seconds = timeout_seconds
        self.interval_seconds = interval_seconds

    @staticmethod
    def on_read(maxAttempts=None, timeoutSeconds=None, intervalSeconds=None):
        return RetrySettings(max_attempts=maxAttempts, timeout_seconds=timeoutSeconds, interval_seconds=intervalSeconds)

    def on_write(self):
        return {
            'maxAttempts': self.max_attempts, 
            'timeoutSeconds': self.timeout_seconds,
            'intervalSeconds': self.interval_seconds
        }

    def __str__(self):
        return f'{self.__class__.__name__}(max_attempts: {self.max_attempts}, timeout_seconds: {self.timeout_seconds}, interval_seconds: {self.interval_seconds})'

    def __repr__(self):
        return f'{self.__class__.__name__}(max_attempts: {self.max_attempts!r}, timeout_seconds: {self.timeout_seconds!r}, interval_seconds: {self.interval_seconds!r})'


    