from .defaults import  DEFAULT_CRD_API_VERSION
from .mod_director import KubeModDirector, READ_ACTION, LIST_ACTION
from .exceptions import ClientMethodNotFoundError
from kubedriver.utils.lru import LRUCache

class CrdDirector:

    def __init__(self, base_kube_client, crd_api_version=DEFAULT_CRD_API_VERSION, cache_capacity=100):
        self.base_kube_client = base_kube_client
        self.mod_director = KubeModDirector()
        self.crd_api_version = crd_api_version
        self.crd_api_client = self.mod_director.build_api_client_for_version(self.crd_api_version, self.base_kube_client)
        found, self._list_crds = self.mod_director.try_plain_method(self.crd_api_client, LIST_ACTION, 'custom_resource_definition')
        if not found:
            raise ClientMethodNotFoundError(f'Could not find list method for custom_resource_definitions at version {self.crd_api_version} (Client: {self.crd_api_client})')
        found, self._read_crd = self.mod_director.try_plain_method(self.crd_api_client, READ_ACTION, 'custom_resource_definition')
        if not found:
            raise ClientMethodNotFoundError(f'Could not find read method for custom_resource_definitions at version {self.crd_api_version} (Client: {self.crd_api_client})')
        self._cache = LRUCache(capacity=cache_capacity)

    def get_crd_by_api_version(self, group, version):
        crds = self._list_crds()
        for crd in crds.items:
            pass


    def get_crd(self, crd_name):
        crd = self._try_cache(crd_name)
        if crd is None:
            # Nothing in cache
            crd = self._read_crd(crd_name)
            self._cache.add(crd_name, crd)
        return crd
        
    def _try_cache(self, crd_name):
        found, crd = self._cache.get(crd_name)
        if found:
            return crd
        else:
            return None

    