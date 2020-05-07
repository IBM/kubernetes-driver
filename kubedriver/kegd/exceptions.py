

class InvalidKegDeploymentStrategyError(Exception):
    pass

class MissingKegDeploymentStrategyFileError(Exception):
    pass

class PersistenceError(Exception):
    pass

class RecordNotFoundError(Exception):
    pass

class StrategyProcessingError(Exception): 
    pass