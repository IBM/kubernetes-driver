import pprint 
from kubedriver.utils.to_dict import to_dict

class V1alpha1DeploymentReportStatus(object):

    openapi_types = {
        'uid': 'str',
        'keg_name': 'str',
        'operation': 'str',
        'state': 'str',
        'error': 'str'
    }

    attribute_map = {
        'uid': 'uid',
        'keg_name': 'kegName',
        'operation': 'operation',
        'state': 'str',
        'error': 'str'
    }

    def __init__(self, uid=None, keg_name=None, operation=None, state=None, error=None):
        self._uid = None
        self._keg_name = None
        self._operation = None
        self._state = None
        self._error = None
        if uid is not None:
            self._uid = uid
        if keg_name is not None:
            self._keg_name = keg_name
        if operation is not None:
            self._operation = operation
        if state is not None:
            self._state = state
        if error is not None:
            self._error = error

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, uid):
        self._uid = uid

    @property
    def keg_name(self):
        return self._keg_name

    @keg_name.setter
    def keg_name(self, keg_name):
        self._keg_name = keg_name

    @property
    def operation(self):
        return self._operation

    @operation.setter
    def operation(self, operation):
        self._operation = operation
    
    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        self._state = state

    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, error):
        self._error = error

    def to_dict(self):
        return to_dict(self)

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, V1alpha1DeploymentReportStatus):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other