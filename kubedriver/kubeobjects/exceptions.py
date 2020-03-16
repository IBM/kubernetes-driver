
class InvalidObjectConfigurationError(Exception):
    
    def __init__(self, reason, object_data):
        full_message = 'Invalid Object Configuration: {0}  -- Object Configuration: {1}'.format(reason, object_data)
        super().__init__(full_message)
        self.reason = reason
        self.object_data = object_data