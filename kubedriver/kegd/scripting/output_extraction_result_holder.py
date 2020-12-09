import base64 

SUCCESS = 'Success'
FAILED = 'Failed'

class OutputExtractionResultHolder:

    def __init__(self):
        self.status = SUCCESS
        self.outputs = {}
        self.reason = None

    def success(self):
        self.status = SUCCESS

    def failed(self, reason):
        self.status = FAILED
        self.reason = reason

    def setOutput(self, output_name, output_value):
        self.set_output(output_name, output_value)

    def set_output(self, output_name, output_value):
        self.outputs[output_name] = output_value

    def decode(self, encoded_value, encoding='utf-8'):
        if encoded_value == None:
            return None
        bytes_str = base64.b64decode(encoded_value)
        return bytes_str.decode(encoding)

    def has_failed(self):
        return (self.status == FAILED), self.reason

    def __str__(self):
        return f'{self.__class__.__name__}(status: {self.status}, outputs: {self.outputs}, reason: {self.reason})'

    def __repr__(self):
        return f'{self.__class__.__name__}(status: {self.status!r}, outputs: {self.outputs!r}, reason: {self.reason!r}'
