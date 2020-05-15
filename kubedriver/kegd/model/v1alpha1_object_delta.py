import pprint 
from kubedriver.utils.to_dict import to_dict

class V1alpha1ObjectDelta(object):

    openapi_types = {
        'group': 'str',
        'kind': 'str',
        'namespace': 'str',
        'name': 'str'
    }

    attribute_map = {
        'group': 'group',
        'kind': 'kind',
        'namespace': 'namespace',
        'name': 'name',
    }

    def __init__(self, group=None, kind=None, name=None, namespace=None):
        self._group = None
        self._kind = None
        self._namespace = None
        self._name = None
        if group is not None:
            self._group = group
        if kind is not None:
            self._kind = kind
        if namespace is not None:
            self._namespace = namespace
        if name is not None:
            self._name = name

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

    def to_dict(self):
        return to_dict(self)

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, V1alpha1ObjectDelta):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other