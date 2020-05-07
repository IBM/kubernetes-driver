from ignition.service.framework import Service, Capability
from kubedriver.kubeclient import KubeApiController
from .context import LocationContext

class LocationContextFactory(Service, Capability):

    def __init__(self, client_director, kegd_persister_factory, keg_persister_factory):
        self.client_director = client_director
        self.kegd_persister_factory = kegd_persister_factory
        self.keg_persister_factory = keg_persister_factory
    
    def build_context(self, kube_location):
        client = self.__build_client(kube_location)
        api_ctl = self.__build_api_ctl(kube_location, client)
        kegd_persister = self.kegd_persister_factory.build(kube_location, api_ctl)
        keg_persister = self.keg_persister_factory.build(kube_location, api_ctl)
        return LocationContext(kube_location=kube_location, api_ctl=api_ctl, kegd_persister=kegd_persister, keg_persister=keg_persister)    

    def __build_client(self, kube_location):
        return kube_location.client

    def __build_api_ctl(self, kube_location, kube_client):
        kwargs = {}
        if kube_location.crd_api_version is not None:
            kwargs['crd_api_version'] = kube_location.crd_api_version
        return KubeApiController(kube_client, self.client_director, default_namespace=kube_location.default_object_namespace, **kwargs)
