
class InvalidResourceConfigurationError(Exception):
    
    def __init__(self, reason, resource_data):
        full_message = 'Invalid Resource Configuration: {0}  -- Resource Configuration: {1}'.format(reason, resource_data)
        super().__init__(full_message)
        self.reason = reason
        self.resource_data = resource_data