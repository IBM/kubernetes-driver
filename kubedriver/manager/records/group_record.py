from .object_states import ObjectStates
from .object_record import ObjectRecord
from .request_record import RequestRecord

class GroupRecord:

    UID = 'uid'
    OBJECTS = 'objects'
    REQUESTS = 'requests'

    def __init__(self, uid, objects, requests=None):
        self.uid = uid
        self.objects = objects
        self.requests = requests if requests is not None else []

    def __str__(self):
        return f'{self.__class__.__name__}(uid: {self.uid}, objects: {self.objects}, requests: {self.requests})'

    def __repr__(self):
        return f'{self.__class__.__name__}(uid: {self.uid!r}, objects: {self.objects!r}, requests: {self.requests!r})'
