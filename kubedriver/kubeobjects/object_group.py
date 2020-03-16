
class ObjectConfigurationGroup:

    def __init__(self, identifier, objects):
        self.identifier = identifier
        self.objects = objects

    def __str__(self):
        return f'{self.__class__.__name__}(identifier: {self.identifier}, objects: {self.object})'

    def __repr__(self):
        return f'{self.__class__.__name__}(identifier: {self.identifier!r}, objects: {self.object!r})'
