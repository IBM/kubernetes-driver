import pprint 
from kubedriver.utils.to_dict import to_dict

class V1alpha1KegCompositionStatus(object):

    openapi_types = {
        'objects': 'list[V1alpha1ObjectStatus]',
        'helm_releases': 'list[V1alpha1HelmReleaseStatus]',
    }

    attribute_map = {
        'objects': 'objects',
        'helm_releases': 'helmReleases'
    }

    def __init__(self, objects=None, helm_releases=None):
        self._objects = None
        self._helm_releases = None
        if objects is not None:
            self._objects = objects
        if helm_releases is not None:
            self._helm_releases = helm_releases

    @property
    def objects(self):
        return self._objects

    @objects.setter
    def objects(self, objects):
        self._objects = objects

    @property
    def helm_releases(self):
        return self._helm_releases

    @helm_releases.setter
    def helm_releases(self, helm_releases):
        self._helm_releases = helm_releases

    def to_dict(self):
        return to_dict(self)

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, V1alpha1KegCompositionStatus):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other