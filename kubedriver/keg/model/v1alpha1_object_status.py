import pprint 
from kubedriver.utils.to_dict import to_dict

class V1alpha1ObjectStatus(object):

    openapi_types = {
        'group': 'str',
        'kind': 'str',
        'namespace': 'str',
        'name': 'str',
        'uid': 'str',
        'state': 'str',
        'resource_version': 'str',
        'error': 'str',
        'tags': 'dict(str, list[str])'
    }

    attribute_map = {
        'group': 'group',
        'kind': 'kind',
        'namespace': 'namespace',
        'name': 'name',
        'uid': 'uid',
        'state': 'state',
        'error': 'error',
        'resource_version': 'resource_version',
        'tags': 'tags'
    }

    def __init__(self, group=None, kind=None, namespace=None, name=None, uid=None, state=None, error=None, tags=None, resource_version=None):
        self._group = None
        self._kind = None
        self._namespace = None
        self._name = None
        self._uid = None
        self._state = None
        self._error = None
        self._tags = None
        self._resource_version = None
        if group is not None:
            self._group = group
        if kind is not None:
            self._kind = kind
        if namespace is not None:
            self._namespace = namespace
        if name is not None:
            self._name = name
        if uid is not None:
            self._uid = uid
        if state is not None:
            self._state = state
        if error is not None:
            self._error = error
        if tags is not None:
            self._tags = tags
        if resource_version is not None:
            self._resource_version = resource_version

    @property
    def group(self):
        return self._group

    @group.setter
    def group(self, group):
        self._group = group

    @property
    def kind(self):
        return self._kind

    @kind.setter
    def kind(self, kind):
        self._kind = kind

    @property
    def namespace(self):
        return self._namespace

    @namespace.setter
    def namespace(self, namespace):
        self._namespace = namespace

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def resource_version(self):
        return self._resource_version

    @resource_version.setter
    def resource_version(self, resource_version):
        self._resource_version = resource_version

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, uid):
        self._uid = uid

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
        if not isinstance(other, V1alpha1ObjectStatus):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other