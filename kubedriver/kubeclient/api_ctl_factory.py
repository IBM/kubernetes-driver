from ignition.service.framework import Service, Capability
from .crd_director import CrdDirector
from .client_director import KubeClientDirector
from .api_ctl import KubeApiController

class KubeApiControllerFactory(Service, Capability):

    def build(self, kube_location):
        crd_director = self.__build_crd_director(kube_location)
        client_director = self.__build_client_director(kube_location, crd_director)
        return KubeApiController(client_director, crd_director, default_namespace=kube_location.default_object_namespace)

    def __build_crd_director(self, kube_location):
        kwargs = {}
        if kube_location.crd_api_version is not None:
            kwargs['crd_api_version'] = kube_location.crd_api_version
        return CrdDirector(kube_location.client, **kwargs)

    def __build_client_director(self, kube_location, crd_director):
        return KubeClientDirector(kube_location.client, crd_director)