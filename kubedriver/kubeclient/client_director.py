import kubernetes.client as kubernetes_client_mod
import re
from .defaults import DEFAULT_NAMESPACE, DEFAULT_CRD_API_VERSION
from .exceptions import ClientMethodNotFoundError, UnrecognisedObjectKindError

EXTENSIONS_GROUP_SUFFIX = '.k8s.io'
CORE_GROUP = 'core'
CREATE_ACTION = 'create'
DELETE_ACTION = 'delete'
UPDATE_ACTION = 'replace'
READ_ACTION = 'read'
LIST_ACTION = 'list'

class KubeClientDirector:

    def determine_api_client_for_version(self, api_version):
        api_client_name = self.__determine_api_class_name_for_version(api_version)
        # api_client_name = CoreV1Api -> api_class = kubernetes.client.CoreV1Api
        # api_client_name = ApiextensionsV1beta1Api -> api_class = kubernetes.client.ApiextensionsV1beta1Api
        if hasattr(kubernetes_client_mod, api_client_name):
            return getattr(kubernetes_client_mod, api_client_name)
        else:
            # Must be a custom resource
            return kubernetes_client_mod.CustomObjectsApi

    def determine_api_method_for_create_object(self, base_kube_client, api_version, kind, return_api_client=False):
        return self.__determine_api_method_for_action(base_kube_client, api_version, kind, CREATE_ACTION, return_api_client)
    
    def determine_api_method_for_update_object(self, base_kube_client, api_version, kind, return_api_client=False):
        return self.__determine_api_method_for_action(base_kube_client, api_version, kind, UPDATE_ACTION, return_api_client)
    
    def determine_api_method_for_delete_object(self, base_kube_client, api_version, kind, return_api_client=False):
        return self.__determine_api_method_for_action(base_kube_client, api_version, kind, DELETE_ACTION, return_api_client)
    
    def determine_api_method_for_read_object(self, base_kube_client, api_version, kind, return_api_client=False):
        return self.__determine_api_method_for_action(base_kube_client, api_version, kind, READ_ACTION, return_api_client)
    
    def determine_api_method_for_list_object(self, base_kube_client, api_version, kind, return_api_client=False):
        return self.__determine_api_method_for_action(base_kube_client, api_version, kind, LIST_ACTION, return_api_client)
    
    def __determine_api_method_for_action(self, base_kube_client, api_version, kind, action_type, return_api_client):
        api_client = self.__build_api_client_for_version(api_version, base_kube_client)
        method, is_namespaced, is_custom_object = self.__find_api_method(api_client, kind, action_type)
        if return_api_client:
            return method, is_namespaced, is_custom_object, api_client
        else:
            return method, is_namespaced, is_custom_object
    
    def __build_api_client_for_version(self, api_version, base_kube_client):
        api_class = self.determine_api_client_for_version(api_version)
        return api_class(base_kube_client)

    def parse_api_version(self, api_version):
        # apiVersion: v1 -> group=core, version=v1
        # apiVersion: apiextensions.k8s.io/v1beta1 -> group=apiextensions.k8s.io, version = v1beta1
        group, slash, version = api_version.partition('/')
        if len(version) == 0:
            version = group
            group = CORE_GROUP
        return group, version

    def __determine_api_class_name_for_version(self, api_version):
        resource_group, resource_version = self.parse_api_version(api_version)
        # Remove the k8s.io part
        if EXTENSIONS_GROUP_SUFFIX in resource_group:
            idx = resource_group.rindex(EXTENSIONS_GROUP_SUFFIX)
            resource_group = resource_group[:idx]+resource_group[idx+len(EXTENSIONS_GROUP_SUFFIX):]
        # apiVersion: v1 -> group=core, version=v1 -> api_client_name = CoreV1Api
        # apiVersion: apiextensions.k8s.io/v1beta1 -> group=apiextensions.k8s.io, version = v1beta1 -> api_client_name = ApiextensionsV1beta1Api
        group_parts = resource_group.split('.')
        api_client_name = ''
        for part in group_parts:
            api_client_name += part.capitalize()
        api_client_name += resource_version.capitalize()
        api_client_name += 'Api'
        return api_client_name

    def __convert_kind_to_method_ready(self, kind):
        kind = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', kind)
        kind = re.sub('([a-z0-9])([A-Z])', r'\1_\2', kind).lower()
        return kind

    def __try_namespaced_method(self, api_client, action_type, method_ready_kind):
        namespaced_method_name = '{0}_namespaced_{1}'.format(action_type, method_ready_kind)
        found = hasattr(api_client, namespaced_method_name)
        if found:
            return found, getattr(api_client, namespaced_method_name)
        return found, None

    def __try_plain_method(self, api_client, action_type, method_ready_kind):
        plain_method_name = '{0}_{1}'.format(action_type, method_ready_kind)
        found = hasattr(api_client, plain_method_name)
        if found:
            return found, getattr(api_client, plain_method_name)
        return found, None

    def __find_api_method(self, api_client, kind, action_type):
        if api_client.__class__ == kubernetes_client_mod.CustomObjectsApi:
            method, is_namespaced = self.__find_custom_object_api_method(api_client, kind, action_type)
            return method, is_namespaced, True
        else:
            method, is_namespaced = self.__find_builtin_api_method(api_client, kind, action_type)
            return method, is_namespaced, False

    def __find_builtin_api_method(self, api_client, kind, action_type):
        method_ready_kind = self.__convert_kind_to_method_ready(kind)
        is_namespaced, method = self.__try_namespaced_method(api_client, action_type, method_ready_kind)
        if not is_namespaced:
            is_plain, method = self.__try_plain_method(api_client, action_type, method_ready_kind)
            if not is_plain:
                raise ClientMethodNotFoundError('Cannot determine method for action \'{0}\' of kind \'{1}\' in Api client \'{2}\''.format(action_type, kind, api_client.__class__))
        return method, is_namespaced

    def __find_custom_object_api_method(self, api_client, kind, action_type):
        method_ready_kind = 'custom_object'
        if action_type == READ_ACTION:
            action_type = 'get' #custom objects have a different verb
        is_namespaced, method = self.__try_namespaced_method(api_client, action_type, method_ready_kind)
        if not is_namespaced:
            raise ClientMethodNotFoundError('Cannot determine method for action \'{0}\' of custom object kind \'{1}\' in Api client \'{2}\''.format(action_type, kind, api_client.__class__))
        return method, is_namespaced
