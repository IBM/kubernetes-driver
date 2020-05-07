from ignition.service.framework import Service, Capability
from kubedriver.persistence import ConfigMapPersistence, CmRecordBuilder
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
        return ConfigMapPersistence('Keg', api_ctl, kube_location.driver_namespace, record_builder, 
                                    cm_api_version=kube_location.cm_api_version, cm_kind=kube_location.cm_kind, 
                                    cm_data_field=kube_location.cm_data_field)

    def __build_record_builder(self, kube_location):
        return CmRecordBuilder(kube_location.client, data_types)
