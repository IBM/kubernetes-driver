import pprint 
from kubedriver.utils.to_dict import to_dict

class V1alpha1HelmReleaseStatus(object):
    
    openapi_types = {
        'name': 'str',
        'namespace': 'str',
        'state': 'str',
        'error': 'str',
        'tags': 'dict(str, list[str])'
    }

    attribute_map = {
        'name': 'name',
        'namespace': 'namespace',
        'state': 'state',
        'error': 'error',
        'tags': 'tags'
    }

    def __init__(self, name=None, namespace=None, state=None, error=None, tags=None):
        self._name = None
        self._namespace = None
        self._state = None
        self._error = None
        self._tags = None
        if name is not None:
            self._name = name
        if namespace is not None:
            self._namespace = namespace
        if state is not None:
            self._state = state
        if error is not None:
            self._error = error
        if tags is not None:
            self._tags = tags
    
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def namespace(self):
        return self._namespace

    @namespace.setter
    def namespace(self, namespace):
        self._namespace = namespace

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
    
    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, tags):
        self._tags = tags

    def to_dict(self):
        return to_dict(self)

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, V1alpha1HelmReleaseStatus):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other