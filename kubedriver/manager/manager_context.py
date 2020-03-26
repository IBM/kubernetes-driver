from ignition.service.framework import Service, Capability, interface
from kubedriver.kubeclient import KubeApiController, KubeClientDirector
from kubedriver.manager import ConfigMapRecordPersistence

class ManagerContext:

    def __init__(self, location, api_ctl, record_persistence):
        self.location = location
        self.api_ctl = api_ctl
        self.record_persistence = record_persistence

class ManagerContextLoader(Service, Capability):

    def __init__(self, client_director):
        self.client_director = client_director

    def load(self, kube_location):
        kube_client = self.__build_client(kube_location)
        api_ctl = self.__build_api_ctl(kube_location, kube_client)
        record_persistence = self.__build_persistence(kube_location, api_ctl)
        return ManagerContext(kube_location, api_ctl, record_persistence)

    def __build_client(self, kube_location):
        return kube_location.build_client()

    def __build_api_ctl(self, kube_location, kube_client):
        kwargs = {}
        if kube_location.crd_api_version is not None:
            kwargs['crd_api_version'] = kube_location.crd_api_version
        return KubeApiController(kube_client, self.client_director, default_namespace=kube_location.default_object_namespace, **kwargs)

    def __build_persistence(self, kube_location, api_ctl):
        storage_namespace = kube_location.driver_namespace
        kwargs = {}
        if kube_location.cm_api_version is not None:
            kwargs['cm_api_version'] = kube_location.cm_api_version
        if kube_location.cm_kind is not None:
            kwargs['cm_kind'] = kube_location.cm_kind
        if kube_location.cm_data_field is not None:
            kwargs['cm_data_field'] = kube_location.cm_data_field        
        return ConfigMapRecordPersistence(api_ctl, storage_namespace, **kwargs)
