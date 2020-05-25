from ignition.service.framework import Service, Capability
from .os_api_ctl import OpenshiftApiController

class OpenshiftApiControllerFactory(Service, Capability):

    def build(self, kube_location):
        return OpenshiftApiController(kube_location.client, default_namespace=kube_location.default_object_namespace)
