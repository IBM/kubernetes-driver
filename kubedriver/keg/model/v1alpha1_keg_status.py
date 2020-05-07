import pprint 
from kubedriver.utils.to_dict import to_dict


class V1alpha1KegStatus(object):

    openapi_types = {
        'composition': 'V1alpha1KegCompositionStatus'
    }

    attribute_map = {
        'composition': 'composition'
    }

    def __init__(self, composition=None):
        self._composition = None
        self._requests = None
        if composition is not None:
            self._composition = composition

    @property
    def composition(self):
        return self._composition

    @composition.setter
    def composition(self, composition):
        self._composition = composition
    
    def to_dict(self):
        return to_dict(self)

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, V1alpha1KegStatus):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other
       