from .retry_settings import RetrySettings
from .exceptions import InvalidDeploymentStrategyError

class ReadyCheck:

    def __init__(self, script, retry_settings=None):
        if script == None:
            raise InvalidDeploymentStrategyError('Ready check requires \'script\' to be set')
        self.script = script
        self.retry_settings = retry_settings
    
    @staticmethod
    def on_read(script=None, **kwargs):
        parsed_retry_settings = None
        if len(kwargs) != 0:
            parsed_retry_settings = RetrySettings.on_read(**kwargs)
        return ReadyCheck(script=script, retry_settings=parsed_retry_settings)

    def on_write(self):
        data = {
            'script': self.script
        }
        if self.retry_settings != None:
            data.update(self.retry_settings.on_write())
        return data


