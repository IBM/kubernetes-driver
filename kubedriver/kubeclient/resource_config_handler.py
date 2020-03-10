import kubernetes.client as kubernetes_client_mod
from .exceptions import InvalidResourceConfiguration

DEFAULT_NAMESPACE = 'default'
DEFAULT_CRD_API_VERSION = 'apiextensions.k8s.io/v1beta1'

class ResourceConfigurationHandler:

    def __init__(self, kube_client, resource_api_converter):
        self.kube_client = kube_client
        self.resource_api_converter = resource_api_converter

    def create_resources(self, resource_configs, default_namespace=DEFAULT_NAMESPACE, crd_api_version=DEFAULT_CRD_API_VERSION):
        for resource_config in resource_configs:
            self.create_resource(resource_config, default_namespace=default_namespace, crd_api_version=crd_api_version)

    def create_resource(self, resource_config, default_namespace=DEFAULT_NAMESPACE, crd_api_version=DEFAULT_CRD_API_VERSION):
        api_client = self.resource_api_converter.build_api_client_for(self.kube_client, resource_config.api_version)
        api_method, is_namespaced = self.resource_api_converter.determine_api_create_method(api_client, resource_config.kind)
        self.__make_create_api_call(api_client, api_method, is_namespaced, resource_config, default_namespace, crd_api_version)

    def get_resource(self, apiVersion, kind, name, namespace=DEFAULT_NAMESPACE):
        pass

    def __make_create_api_call(self, api_client, api_method, is_namespaced, resource_config, default_namespace, crd_api_version):
        if api_client.__class__ == kubernetes_client_mod.CustomObjectsApi:
            arguments = self.__build_customobj_create_arguments(is_namespaced, resource_config, default_namespace, crd_api_version)
        else:
            arguments = self.__build_builtin_create_arguments(is_namespaced, resource_config, default_namespace)
        api_method(**arguments)

    def __build_builtin_create_arguments(self, is_namespaced, resource_config, default_namespace):
        args = {
            'body': resource_config.resource_data
        }
        if is_namespaced:
            args['namespace'] = self.__determine_namespace(resource_config, default_namespace)
        return args

    def __build_customobj_create_arguments(self, is_namespaced, resource_config, default_namespace, crd_api_version):
        group, version = self.resource_api_converter.read_api_version(resource_config.api_version)
        plural = self.__determine_plural(crd_api_version, group, version, resource_config.kind)
        args = {
            'group': group,
            'version': version,
            'plural': plural,
            'body': resource_config.resource_data
        }
        if is_namespaced:
            args['namespace'] = self.__determine_namespace(resource_config, default_namespace)
        return args

    def __determine_namespace(self, resource_config, default_namespace):
        if 'namespace' in resource_config.metadata:
            return resource_config.metadata.get('namespace')
        else:
            return default_namespace

    def __determine_plural(self, crd_api_version, group, version, kind):
        extensions_api = self.resource_api_converter.build_api_client_for(crd_api_version)
        crds = extensions_api.list_custom_resource_definition(field_selector='spec.group={0},spec.names.kind={1}'.format(group, kind))
        plural = None
        for crd in crds:
            is_version_match = crd.version == version
            if not is_version_match:
                crd_versions = crd.versions
                for crd_version in crd_versions:
                    if crd_version.name == version:
                        is_version_match = True
                        break
            if is_version_match:
                plural = crd.spec.names.plural
                break
        if plural is None:
            raise InvalidResourceConfiguration('Could not find a CRD for custom Resource with group \'{0}\', version \'{1}\', kind \'{2}\''.format(group, version, kind))
        return plural