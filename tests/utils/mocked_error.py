
class MockedError(Exception):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def default(self):
        return MockedError('A mocked error')