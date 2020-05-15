from ignition.service.framework import Service, Capability
from kubedriver.persistence import ConfigMapPersister, CmRecordBuilder
from kubedriver.kubeclient import KubeApiController
from kubedriver.keg.model import (V1alpha1HelmReleaseStatus, V1alpha1Keg, V1alpha1KegCompositionStatus,
                                    V1alpha1KegStatus, V1alpha1ObjectStatus)

data_types = {}
data_types['V1alpha1HelmReleaseStatus'] = V1alpha1HelmReleaseStatus
data_types['V1alpha1Keg'] = V1alpha1Keg
data_types['V1alpha1KegCompositionStatus'] = V1alpha1KegCompositionStatus
data_types['V1alpha1KegStatus'] = V1alpha1KegStatus
data_types['V1alpha1ObjectStatus'] = V1alpha1ObjectStatus

class KegPersistenceFactory(Service, Capability):


    def build(self, kube_location, api_ctl):
        record_builder = self.__build_record_builder(kube_location)
        cm_persister_args = kube_location.get_cm_persister_args()
        return ConfigMapPersister('Keg', api_ctl, kube_location.driver_namespace, record_builder, 
                                    **cm_persister_args)

    def __build_record_builder(self, kube_location):
        return CmRecordBuilder(kube_location.client, V1alpha1KegStatus, data_types)
