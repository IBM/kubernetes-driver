from ignition.service.framework import Service, Capability
from .deployment_location import KubernetesDeploymentLocation

class KubernetesDeploymentLocationTranslator(Service, Capability):

    def translate(self, dl_dict):
        return KubernetesDeploymentLocation.from_dict(dl_dict)