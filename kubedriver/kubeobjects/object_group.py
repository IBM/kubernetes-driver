
class ObjectConfigurationGroup:

    def __init__(self, identifier, objects=None, helm_releases=None):
        self.identifier = identifier
        self.objects = objects if objects is not None else []
        self.helm_releases = helm_releases if helm_releases is not None else []

    def __str__(self):
        return f'{self.__class__.__name__}(identifier: {self.identifier}, objects: {self.objects}, helm_releases: {self.helm_releases})'

    def __repr__(self):
        return f'{self.__class__.__name__}(identifier: {self.identifier!r}, objects: {self.objects!r}, helm_releases: {self.helm_releases!r})'
