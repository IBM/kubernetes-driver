from .retry_settings import RetrySettings

class RetryStatus:

    def __init__(self, current_task, settings, attempts=0, start_time=None, recent_attempt_times=None):
        self.current_task = current_task
        self.settings = settings
        self.attempts = attempts
        self.start_time = start_time
        self.recent_attempt_times = recent_attempt_times if recent_attempt_times is not None else []

    @staticmethod
    def on_read(currentTask=None, settings=None, attempts=0, startTime=None, recentAttemptTimes=None):
        parsed_settings = None
        if settings != None:
            parsed_settings = RetrySettings.on_read(**settings)
        return RetryStatus(current_task=currentTask, settings=parsed_settings, attempts=attempts, start_time=startTime, recent_attempt_times=recentAttemptTimes)

    def on_write(self):
        write_settings = None
        if self.settings != None:
            write_settings = self.settings.on_write()
        return {
            'currentTask': self.current_task,
            'settings': write_settings, 
            'attempts': self.attempts,
            'startTime': self.start_time, 
            'recentAttemptTimes': self.recent_attempt_times
        }

    def __str__(self):
        return f'{self.__class__.__name__}(current_task: {self.current_task}, settings: {self.settings}, attempts: {self.attempts}, start_time: {self.start_time}, recent_attempt_times: {self.recent_attempt_times})'

    def __repr__(self):
        return f'{self.__class__.__name__}(current_task: {self.current_task!r}, settings: {self.settings!r}, attempts: {self.attempts!r}, start_time: {self.start_time!r}, recent_attempt_times: {self.recent_attempt_times!r})'
    