import re
from .api_version_parser import ApiVersionParser

EXTENSIONS_GROUP_SUFFIX = '.k8s.io'
CORE_GROUP = 'core'
CREATE_ACTION = 'create'
DELETE_ACTION = 'delete'
UPDATE_ACTION = 'replace'
READ_ACTION = 'read'
GET_ACTION = 'get'
LIST_ACTION = 'list'
API_CLIENT_CLASS_SUFFIX = 'Api'

class KubeModDirector:

    def __init__(self):
        self.api_version_parser = ApiVersionParser()
    
    def get_api_client_class_name_for_version(self, api_version):
        resource_group, resource_version = self.api_version_parser.parse(api_version)
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
        api_client_name += API_CLIENT_CLASS_SUFFIX
        return api_client_name

    def get_api_client_class_for_version(self, api_version):
        api_client_name = self.get_api_client_class_name_for_version(api_version)
        # api_client_name = CoreV1Api -> api_class = kubernetes.client.CoreV1Api
        # api_client_name = ApiextensionsV1beta1Api -> api_class = kubernetes.client.ApiextensionsV1beta1Api
        if hasattr(kubernetes_client_mod, api_client_name):
            return getattr(kubernetes_client_mod, api_client_name)
        else:
            # Must be a custom resource
            return kubernetes_client_mod.CustomObjectsApi

    def build_api_client_for_version(self, api_version, base_kube_client):
        api_class = self.get_api_client_class_for_version(api_version)
        return api_class(base_kube_client)

    def convert_kind_to_method_ready(self, kind):
        if kind == ''
        # Lower case and split camel case to snake_case
        kind = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', kind)
        kind = re.sub('([a-z0-9])([A-Z])', r'\1_\2', kind).lower()
        return kind

    def try_namespaced_method(self, api_client, action_type, kind):
        method_ready_kind = self.convert_kind_to_method_ready(kind)
        namespaced_method_name = '{0}_namespaced_{1}'.format(action_type, method_ready_kind)
        found = hasattr(api_client, namespaced_method_name)
        if found:
            return found, getattr(api_client, namespaced_method_name)
        return found, None

    def try_plain_method(self, api_client, action_type, kind):
        method_ready_kind = self.convert_kind_to_method_ready(kind)
        plain_method_name = '{0}_{1}'.format(action_type, method_ready_kind)
        found = hasattr(api_client, plain_method_name)
        if found:
            return found, getattr(api_client, plain_method_name)
        return found, None
    
    def try_cluster_method(self, api_client, action_type, kind):
        method_ready_kind = self.convert_kind_to_method_ready(kind)
        method_name = '{0}_cluster_{1}'.format(action_type, method_ready_kind)
        found = hasattr(api_client, method_name)
        if found:
            return found, getattr(api_client, method_name)
        return found, None