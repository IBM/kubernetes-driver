from ignition.service.framework import Service, Capability
from kubedriver.persistence import ConfigMapPersister, CmRecordBuilder
from kubedriver.kubeclient import KubeApiController
from kubedriver.kegd.model import (V1alpha1KegDeploymentReport, V1alpha1KegDeploymentReportStatus)

data_types = {}
data_types['V1alpha1KegDeploymentReport'] = V1alpha1KegDeploymentReport
data_types['V1alpha1KegDeploymentReportStatus'] = V1alpha1KegDeploymentReportStatus

class KegdReportPersistenceFactory(Service, Capability):

    def build(self, kube_location, api_ctl):
        record_builder = self.__build_record_builder(kube_location)
        cm_persister_args = kube_location.get_cm_persister_args()
        return ConfigMapPersister('KegDeploymentReport', api_ctl, kube_location.driver_namespace, record_builder, 
                                    **cm_persister_args)

    def __build_record_builder(self, kube_location):
        return CmRecordBuilder(kube_location.client, V1alpha1KegDeploymentReportStatus, data_types)
