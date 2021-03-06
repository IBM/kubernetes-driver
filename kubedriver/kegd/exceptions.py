
class MissingKegDeploymentStrategyFileError(Exception):
    pass

class StrategyProcessingError(Exception): 
    pass

class MultiErrorStrategyProcessingError(StrategyProcessingError):

    def __init__(self, message, original_errors, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        self.original_errors = original_errors