from ignition.service.framework import Service, Capability
from kubedriver.kubeclient import KubeApiController, KubeClientDirector, CrdDirector
from .context import LocationContext

class LocationContextFactory(Service, Capability):

    def __init__(self, api_ctl_factory, kegd_persister_factory, keg_persister_factory):
        self.api_ctl_factory = api_ctl_factory
        self.kegd_persister_factory = kegd_persister_factory
        self.keg_persister_factory = keg_persister_factory
    
    def build(self, kube_location):
        api_ctl = self.api_ctl_factory.build(kube_location)
        kegd_persister = self.kegd_persister_factory.build(kube_location, api_ctl)
        keg_persister = self.keg_persister_factory.build(kube_location, api_ctl)
        return LocationContext(kube_location=kube_location, api_ctl=api_ctl, kegd_persister=kegd_persister, keg_persister=keg_persister)    
