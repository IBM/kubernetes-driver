import pprint 
from kubedriver.utils.to_dict import to_dict

class V1alpha1KegdCompositionDelta(object):

    openapi_types = {
        'deployed': 'V1alpha1KegdCompositionDeltaSubset',
        'removed': 'V1alpha1KegdCompositionDeltaSubset',
    }

    attribute_map = {
        'deployed': 'deployed',
        'removed': 'removed'
    }

    def __init__(self, deployed=None, removed=None):
        self._deployed = None
        self._removed = None
        if deployed is not None:
            self._deployed = deployed
        if removed is not None:
            self._removed = removed

    @property
    def deployed(self):
        return self._deployed

    @deployed.setter
    def deployed(self, deployed):
        self._deployed = deployed

    @property
    def removed(self):
        return self._removed

    @removed.setter
    def removed(self, removed):
        self._removed = removed

    def to_dict(self):
        return to_dict(self)

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, V1alpha1KegdCompositionDelta):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other