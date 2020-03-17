import uuid
from .object_records import DeployedObjectRecord, DeployedObjectGroupRecord
from kubedriver.kubeclient.defaults import DEFAULT_NAMESPACE

class KubeObjectManager:

    def __init__(self, kube_api_ctl, record_persistence, default_namespace=DEFAULT_NAMESPACE):
        self.kube_api_ctl = kube_api_ctl
        self.record_persistence = record_persistence
        self.default_namespace = default_namespace

    def create_object_group(self, object_group):
        self.__persist_group_record(object_group)
        #TODO: Errors here mean we have a group persisted that will never be cleared?
        self.__create_group_objects(object_group)

    def get_object_group_record(self, identifier):
        object_group_record = self.record_persistence.get_object_group_record(identifier)
        return object_group_record

    def delete_object_group(self, identifier):
        object_group_record = self.record_persistence.get_object_group_record(identifier)
        #TODO: Again, error handling?
        self.__delete_recorded_objects(object_group_record)
        self.record_persistence.delete_object_group_record(identifier)

    def __create_group_objects(self, object_group):
        for object_conf in object_group.objects:
            self.kube_api_ctl.create_object(object_conf, default_namespace=self.default_namespace)

    def __delete_recorded_objects(self, object_group_record):
        for object_record in object_group_record.object_records:
            self.kube_api_ctl.delete_object(object_record.api_version, object_record.kind, object_record.name, namespace=object_record.namespace)

    def __persist_group_record(self, object_group):
        group_record = self.__build_group_record(object_group)
        self.record_persistence.persist_object_group_record(group_record)

    def __build_group_record(self, object_group):
        object_records = []
        for object_conf in object_group.objects:
            is_namespaced = self.kube_api_ctl.is_object_namespaced(object_conf.api_version, object_conf.kind)
            if is_namespaced:
                namespace = object_conf.namespace
                if namespace is None:
                    namespace = self.default_namespace
            else:
                namespace = None
            object_records.append(DeployedObjectRecord(object_conf.api_version, object_conf.kind, namespace, object_conf.name))
        return DeployedObjectGroupRecord(object_group.identifier, object_records)