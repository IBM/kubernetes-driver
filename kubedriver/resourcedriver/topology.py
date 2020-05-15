import json
from ignition.model.associated_topology import AssociatedTopologyEntry, AssociatedTopology


# Chosen because Kubernetes names cannot have colons in them, so seems like a safe choice
SEPERATOR_CHAR = ':'
HELM_TYPE = 'Helm'

class KubeAssociatedTopology(AssociatedTopology):

    def add_object(self, object_delta):
        obj_type = self._build_type_name(object_delta.group, object_delta.kind)
        obj_name = self._build_object_name(object_delta.name, namespace=object_delta.namespace)
        obj_unique_name = self._build_unique_reference(obj_type, obj_name)
        self.add_entry(name=obj_unique_name, element_id=object_delta.uid, element_type=obj_type)

    def add_removed_object(self, object_delta):
        obj_type = self._build_type_name(object_delta.group, object_delta.kind)
        obj_name = self._build_object_name(object_delta.name, namespace=object_delta.namespace)
        obj_unique_name = self._build_unique_reference(obj_type, obj_name)
        self.add_removed(obj_unique_name)

    def add_helm_release(self, helm_release_delta):
        entry_type = HELM_TYPE
        identifier = self._build_helm_name(helm_release_delta.name, helm_release_delta.namespace)
        unique_name = self._build_unique_reference(entry_type, identifier)
        self.add_entry(name=unique_name, element_id=unique_name, element_type=entry_type)

    def add_removed_helm_release(self, helm_release_delta):
        entry_type = HELM_TYPE
        identifier = self._build_helm_name(helm_release_delta.name, helm_release_delta.namespace)
        unique_name = self._build_unique_reference(entry_type, identifier)
        self.add_removed(unique_name)

    def _build_type_name(self, api_version, kind):
        return api_version + SEPERATOR_CHAR + kind

    def _build_object_name(self, name, namespace=None):
        if namespace == None:
            return name
        else:
            return namespace + SEPERATOR_CHAR + name

    def _build_unique_reference(self, type_str, name):
        return type_str + SEPERATOR_CHAR + name

    def _build_helm_name(self, name, namespace):
        return namespace + SEPERATOR_CHAR + name

        
