from ignition.service.framework import Service, Capability
from kubedriver.location import KubernetesDeploymentLocation

class KubeDeploymentLocationTranslatorCapability(Capability):

    def translate(self, dl_dict):
        pass

class KubeDeploymentLocationTranslator(Service, KubeDeploymentLocationTranslatorCapability):

    def translate(self, dl_dict):
        return KubernetesDeploymentLocation.from_dict(dl_dict)