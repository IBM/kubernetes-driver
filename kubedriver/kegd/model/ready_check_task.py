from .retry_settings import RetrySettings

class ReadyCheckTask:

    def __init__(self, script, script_file_name, retry_settings=None):
        self.script = script
        self.script_file_name = script_file_name
        self.retry_settings = retry_settings if retry_settings is not None else RetrySettings()
    
    @staticmethod
    def on_read(script=None, scriptFileName=None, retry=None):
        parsed_retry_settings = None
        if retry != None:
            parsed_retry_settings = RetrySettings.on_read(**retry)
        return ReadyCheckTask(script=script, script_file_name=scriptFileName, retry_settings=parsed_retry_settings)

    def on_write(self):
        write_retry_settings = None
        if self.retry_settings != None:
            write_retry_settings = self.retry_settings.on_write()
        return {
            'script': self.script,
            'scriptFileName': self.script_file_name,
            'retry': write_retry_settings
        }