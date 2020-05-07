
class InvalidObjectConfigurationError(Exception):
    
    def __init__(self, reason, object_data):
        full_message = 'Invalid Object Configuration: {0}  -- Object Configuration: {1}'.format(reason, object_data)
        super().__init__(full_message)
        self.reason = reason
        self.object_data = object_data

class InvalidObjectConfigurationDocumentError(Exception):
    
    def __init__(self, reason, doc_data):
        full_message = 'Invalid Object Configuration Document: {0}  -- Object Configuration Document: {1}'.format(reason, doc_data)
        super().__init__(full_message)
        self.reason = reason
        self.doc_data = doc_data