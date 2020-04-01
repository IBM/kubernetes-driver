import copy
from .copy_args_mock import CopyArgsMagicMock

def create():
    mock_persistence = CopyArgsMagicMock()
    worker = MemoryPersistenceWorker()
    worker.bind_to(mock_persistence)
    return mock_persistence

class MemoryPersistenceWorker():

    def __init__(self, *args, **kwargs):
        self.store = {}

    def bind_to(self, mock):
        mock.create.side_effect = self.create
        mock.get.side_effect = self.get
        mock.delete.side_effect = self.delete
        mock.update.side_effect = self.update

    def create(self, group_record):
        self.store[group_record.uid] = copy.deepcopy(group_record)

    def get(self, uid):
        if uid not in self.store:
            raise ValueError('Mock persistence has not been configured with group with uid: {0}'.format(uid))
        return copy.deepcopy(self.store[uid])

    def delete(self, uid):
        if uid not in self.store:
            raise ValueError('Mock persistence has not been configured with group with uid: {0}'.format(uid))
        self.store.pop(uid)

    def update(self, group_record):
        if group_record.uid not in self.store:
            raise ValueError('Mock persistence has not been configured with group with uid: {0}'.format(uid))
        self.store[group_record.uid] = copy.deepcopy(group_record)
