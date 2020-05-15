from .exceptions import InvalidDeploymentStrategyError

class OutputExtraction:

    def __init__(self, script):
        if script == None:
            raise InvalidDeploymentStrategyError('Extract output definition requires \'script\' to be set')
        self.script = script

    @staticmethod
    def on_read(script=None):
        return OutputExtraction(script=script)

    def on_write(self):
        return {
            'script': self.script
        }
