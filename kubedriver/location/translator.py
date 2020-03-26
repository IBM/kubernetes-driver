from ignition.service.framework import Service, Capability
from .deployment_location import KubeDeploymentLocation

class KubeDeploymentLocationTranslator(Service, Capability):

    def translate(self, dl_dict):
        return KubeDeploymentLocation.from_dict(dl_dict)