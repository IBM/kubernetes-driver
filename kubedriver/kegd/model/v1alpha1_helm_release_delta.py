import pprint 
from kubedriver.utils.to_dict import to_dict

class V1alpha1HelmReleaseDelta(object):
    
    openapi_types = {
        'name': 'str',
        'namespace': 'str',
        'objects_only': 'bool',
        'deployed_objects': 'list[V1alpha1ObjectDelta]',
        'removed_objects': 'list[V1alpha1ObjectDelta]'
    }

    attribute_map = {
        'name': 'name',
        'namespace': 'namespace',
        'objects_only': 'objectsOnly',
        'deployed_objects': 'deployedObjects',
        'removed_objects': 'removedObjects'
    }

    def __init__(self, name=None, namespace=None, objects_only=None, deployed_objects=None, removed_objects=None):
        self._name = None
        self._namespace = None
        self._objects_only = None
        self._deployed_objects = None
        self._removed_objects = None
        if name is not None:
            self._name = name
        if namespace is not None:
            self._namespace = namespace
        if objects_only is not None:
            self._objects_only = objects_only
        if deployed_objects is not None:
            self._deployed_objects = deployed_objects
        if removed_objects is not None:
            self._removed_objects = removed_objects
    
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
    def objects_only(self):
        return self._objects_only

    @objects_only.setter
    def objects_only(self, objects_only):
        self._objects_only = objects_only

    @property
    def deployed_objects(self):
        return self._deployed_objects

    @deployed_objects.setter
    def deployed_objects(self, deployed_objects):
        self._deployed_objects = deployed_objects

    @property
    def removed_objects(self):
        return self._removed_objects

    @removed_objects.setter
    def removed_objects(self, removed_objects):
        self._removed_objects = removed_objects

    def to_dict(self):
        return to_dict(self)

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, V1alpha1HelmReleaseDelta):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other