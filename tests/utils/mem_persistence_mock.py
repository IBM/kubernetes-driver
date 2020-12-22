import copy
import uuid
from .copy_args_mock import CopyArgsMagicMock
from kubedriver.persistence.exceptions import RecordNotFoundError

def create():
    mock_persistence = CopyArgsMagicMock()
    worker = MemoryPersistenceWorker()
    worker.bind_to(mock_persistence)
    return mock_persistence

class MemoryPersistenceWorker():

    def __init__(self, *args, **kwargs):
        self.store = {}
        self.uids = {}

    def bind_to(self, mock):
        mock.create.side_effect = self.create
        mock.get.side_effect = self.get
        mock.delete.side_effect = self.delete
        mock.update.side_effect = self.update
        mock.build_record_reference.side_effect = self.build_record_reference
        mock.get_record_uid.side_effect = self.get_record_uid

    def build_record_reference(self, uid, record_name):
        return {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': record_name,
                'namespace': 'mem',
                'uid': uid
            }
        }
    
    def get_record_uid(self, record_name):
        return self.uids[record_name]

    def create(self, record_name, record_data, labels=None):
        self.store[record_name] = copy.deepcopy(record_data)
        self.uids[record_name] = str(uuid.uuid4())

    def get(self, record_name):
        if record_name not in self.store:
            raise RecordNotFoundError('Mock persistence has not been configured with record_name: {0}'.format(record_name))
        return copy.deepcopy(self.store[record_name])

    def delete(self, record_name):
        if record_name not in self.store:
            raise RecordNotFoundError('Mock persistence has not been configured with record_name: {0}'.format(record_name))
        self.store.pop(uid)

    def update(self, record_name, record_data):
        if record_name not in self.store:
            raise RecordNotFoundError('Mock persistence has not been configured with record_name: {0}'.format(record_name))
        self.store[record_name] = copy.deepcopy(record_data)
