from .defaults import  DEFAULT_CRD_API_VERSION
from .mod_director import KubeModDirector, READ_ACTION, LIST_ACTION
from .exceptions import ClientMethodNotFoundError
from kubedriver.utils.lru import LRUCache

CLUSTER_SCOPE = 'Cluster'
NAMESPACED_SCOPE = 'Namespaced'

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
        self._type_cache = LRUCache(capacity=cache_capacity)

    def get_crd_by_kind(self, group, kind):
        crd = self._try_cache_by_kind(group, kind)
        if crd is None:
            # Not found in cache
            # Currently have to list all CRDs because we don't know the plural so cannot find by name (name = <plural>.<group>)
            crds = self._list_crds()
            matching_crd = None
            for crd in crds.items:
                if crd.spec.group == group and crd.spec.names.kind == kind:
                    matching_crd = crd
                else:
                    # Might as well build up the cache
                    cache_key = self._build_crd_type_cache_key(crd.spec.group, crd.spec.names.kind)
                    self._type_cache.add(cache_key, crd)
            # Add the match to the cache last so it is the most recently used
            if matching_crd is not None:
                cache_key = self._build_crd_type_cache_key(matching_crd.spec.group, matching_crd.spec.names.kind)
                self._type_cache.add(cache_key, matching_crd)
                crd = matching_crd
        return crd
            
    def _try_cache_by_kind(self, group, kind):
        cache_key = self._build_crd_type_cache_key(group, kind)
        found, crd = self._type_cache.get(cache_key)
        if found:
            return crd
        else:
            return None

    def _build_crd_type_cache_key(self, group, kind):
        return f'{group}/{kind}'

    