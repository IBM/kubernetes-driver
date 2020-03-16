from ignition.service.framework import Service, Capability
from kubedriver.kubeclient import KubeApiController, KubeClientDirector
from kubedriver.manager import ConfigMapRecordPersistence, KubeObjectManager

class LocationBasedManagementCapability(Capability):

    def build_manager(self, deployment_location):
        pass

class LocationBasedManagement(Service, LocationBasedManagementCapability):

    def __init__(self, client_director):
        self.client_director = client_director

    def build_manager(self, deployment_location):
        kube_client = self.__build_client(deployment_location)
        api_ctl = self.__build_api_ctl(deployment_location, kube_client)
        record_persistence = self.__build_persistence(deployment_location, api_ctl)
        object_manager = self.__build_object_manager(deployment_location, api_ctl, record_persistence)
        return object_manager

    def __build_object_manager(self, deployment_location, api_ctl, record_persistence):
        return KubeObjectManager(api_ctl, record_persistence, default_namespace=deployment_location.default_object_namespace)

    def __build_client(self, deployment_location):
        kube_client = deployment_location.build_client()
        return kube_client

    def __build_api_ctl(self, deployment_location, kube_client):
        kwargs = {}
        if deployment_location.crd_api_version is not None:
            kwargs['crd_api_version'] = deployment_location.crd_api_version
        return KubeApiController(kube_client, self.client_director, default_namespace=deployment_location.default_object_namespace, **kwargs)

    def __build_persistence(self, deployment_location, api_ctl):
        storage_namespace = deployment_location.driver_namespace
        kwargs = {}
        if deployment_location.cm_api_version is not None:
            kwargs['cm_api_version'] = deployment_location.cm_api_version
        if deployment_location.cm_kind is not None:
            kwargs['cm_kind'] = deployment_location.cm_kind
        if deployment_location.cm_data_field is not None:
            kwargs['cm_data_field'] = deployment_location.cm_data_field        
        return ConfigMapRecordPersistence(api_ctl, storage_namespace, **kwargs)