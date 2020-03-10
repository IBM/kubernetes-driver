import kubernetes.client as kubernetes_client_mod
import re

EXTENSIONS_GROUP_SUFFIX = 'k8s.io'
CORE_GROUP = 'core'
CREATE_ACTION = 'create'
DELETE_ACTION = 'delete'
UPDATE_ACTION = 'replace'

class ResourceApiConverter:

    def read_api_version(self, api_version):
        # apiVersion: v1 -> group=core, version=v1
        # apiVersion: apiextensions.k8s.io/v1beta1 -> group=apiextensions.k8s.io, version = v1beta1
        group, slash, version = api_version.partition('/')
        if len(version) == 0:
            version = group
            group = CORE_GROUP
        return group, version

    def determine_api_class(self, api_version):
        api_client_name = self.determine_api_class_name(api_version)
        # api_client_name = CoreV1Api -> api_class = kubernetes.client.CoreV1Api
        # api_client_name = ApiextensionsV1beta1Api -> api_class = kubernetes.client.ApiextensionsV1beta1Api
        if hasattr(kubernetes_client_mod, api_client_name):
            return getattr(kubernetes_client_mod, api_client_name)
        else:
            #Must be a custom resource
            return kubernetes_client_mod.CustomObjectsApi

    def determine_api_class_name(self, api_version):
        resource_group, resource_version = self.read_api_version(api_version)
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

    def build_api_client_for(self, base_client, api_version):
        api_class = self.determine_api_class(api_version)
        return api_class(base_client)

    def convert_kind_to_method_ready(self, kind):
        kind = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', kind)
        kind = re.sub('([a-z0-9])([A-Z])', r'\1_\2', kind).lower()
        return kind

    def try_namespaced_method(self, api_client, action_type, method_ready_kind):
        namespaced_method_name = '{0}_namespaced_{1}'.format(action_type, method_ready_kind)
        found = hasattr(api_client, namespaced_method_name)
        if found:
            return found, getattr(api_client, namespaced_method_name)
        return found, None

    def try_plain_method(self, api_client, action_type, method_ready_kind):
        plain_method_name = '{0}_{1}'.format(action_type, method_ready_kind)
        found = hasattr(api_client, plain_method_name)
        if found:
            return found, getattr(api_client, plain_method_name)
        return found, None

    def determine_api_method(self, api_client, kind, action_type):
        if api_client.__class__ == kubernetes_client_mod.CustomObjectsApi:
            return self.__find_customobj_api_method(api_client, kind, action_type)
        else:
            return self.__find_builtin_api_method(api_client, kind, action_type)

    def __find_builtin_api_method(self, api_client, kind, action_type):
        method_ready_kind = self.convert_kind_to_method_ready(kind)
        is_namespaced, method = self.try_namespaced_method(api_client, action_type, method_ready_kind)
        if not is_namespaced:
            is_plain, method = self.try_plain_method(api_client, action_type, method_ready_kind)
            if not is_plain:
                raise ValueError('Cannot determine method for action \'{0}\' of kind \'{1}\' in Api client \'{2}\''.format(action_type, kind, api_client.__class__))
        return method, is_namespaced

    def __find_customobj_api_method(self, api_client, kind, action_type):
        method_ready_kind = 'custom_object'
        is_namespaced, method = self.try_namespaced_method(api_client, action_type, method_ready_kind)
        if not is_namespaced:
            raise ValueError('Cannot determine method for action \'{0}\' of custom object kind \'{1}\' in Api client \'{2}\''.format(action_type, kind, api_client.__class__))
        return method, is_namespaced

    def determine_api_create_method(self, api_client, kind):
        return self.determine_api_method(api_client, kind, CREATE_ACTION)

    def determine_api_update_method(self, api_client, kind):
        return self.determine_api_method(api_client, kind, UPDATE_ACTION)

    def determine_api_delete_method(self, api_client, kind):
        return self.determine_api_method(api_client, kind, DELETE_ACTION)
