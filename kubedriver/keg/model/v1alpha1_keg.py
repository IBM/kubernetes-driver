import pprint 
from kubedriver.utils.to_dict import to_dict

#apiVersion: keg.ibm/v1alpha1
#kind: Keg
class V1alpha1Keg(object):

    openapi_types = {
        'api_version': 'str',
        'kind': 'str',
        'metadata': 'V1ObjectMeta',
        'status': 'V1alpha1KegStatus'
    }

    attribute_map = {
        'api_version': 'apiVersion',
        'kind': 'kind',
        'metadata': 'metadata',
        'status': 'status'
    }
    
    def __init__(self, api_version=None, kind=None, metadata=None, status=None):
        self._api_version = None
        self._kind = None
        self._metadata = None
        self._status = None
        if api_version is not None:
            self.api_version = api_version
        if kind is not None:
            self.kind = kind
        if metadata is not None:
            self.metadata = metadata
        if status is not None:
            self.status = status

    @property
    def api_version(self):
        return self._api_version

    @api_version.setter
    def api_version(self, api_version):
        self._api_version = api_version
    
    @property
    def kind(self):
        return self._kind

    @kind.setter
    def kind(self, kind):
        self._kind = kind
    
    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, metadata):
        self._metadata = metadata

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        self._status = status
    
    def to_dict(self):
        return to_dict(self)

    def to_str(self):
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        return self.to_str()

    def __eq__(self, other):
        if not isinstance(other, V1alpha1Keg):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other