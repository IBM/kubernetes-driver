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
        return ConfigMapPersister('KegDeploymentReport', api_ctl, kube_location.driver_namespace, record_builder, 
                                    cm_api_version=kube_location.cm_api_version, cm_kind=kube_location.cm_kind, 
                                    cm_data_field=kube_location.cm_data_field)

    def __build_record_builder(self, kube_location):
        return CmRecordBuilder(kube_location.client, data_types)
