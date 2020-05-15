from .exceptions import InvalidDeploymentStrategyError

class OutputExtractionTask:

    def __init__(self, script, script_file_name):
        if script == None:
            raise InvalidDeploymentStrategyError('Extract output definition requires \'script\' to be set')
        self.script = script
        self.script_file_name = script_file_name

    @staticmethod
    def on_read(script=None, scriptFileName=None):
        return OutputExtractionTask(script=script, script_file_name=scriptFileName)

    def on_write(self):
        return {
            'script': self.script,
            'scriptFileName': self.script_file_name
        }
