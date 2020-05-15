from ignition.service.framework import Service, Capability
from kubedriver.persistence import ConfigMapPersister, CmRecordBuilder
from kubedriver.kubeclient import KubeApiController
from kubedriver.kegd.model import (V1alpha1KegdStrategyReport, V1alpha1KegdStrategyReportStatus, V1alpha1KegdCompositionDelta,
                                        V1alpha1KegdCompositionDeltaSubset, V1alpha1ObjectDelta, V1alpha1HelmReleaseDelta)

data_types = {}
data_types['V1alpha1KegdStrategyReport'] = V1alpha1KegdStrategyReport
data_types['V1alpha1KegdStrategyReportStatus'] = V1alpha1KegdStrategyReportStatus
data_types['V1alpha1KegdCompositionDelta'] = V1alpha1KegdCompositionDelta
data_types['V1alpha1KegdCompositionDeltaSubset'] = V1alpha1KegdCompositionDeltaSubset
data_types['V1alpha1ObjectDelta'] = V1alpha1ObjectDelta
data_types['V1alpha1HelmReleaseDelta'] = V1alpha1HelmReleaseDelta

class KegdReportPersistenceFactory(Service, Capability):

    def build(self, kube_location, api_ctl):
        record_builder = self.__build_record_builder(kube_location)
        cm_persister_args = kube_location.get_cm_persister_args()
        return ConfigMapPersister('KegDeploymentReport', api_ctl, kube_location.driver_namespace, record_builder, 
                                    **cm_persister_args)

    def __build_record_builder(self, kube_location):
        return CmRecordBuilder(kube_location.client, V1alpha1KegdStrategyReportStatus, data_types)
