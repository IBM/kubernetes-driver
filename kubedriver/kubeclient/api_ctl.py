from .defaults import DEFAULT_NAMESPACE, DEFAULT_CRD_API_VERSION
from .exceptions import UnrecognisedObjectKindError
import kubernetes.client as kubernetes_client_mod

class KubeApiController:

    def __init__(self, base_kube_client, client_director, crd_api_version=DEFAULT_CRD_API_VERSION, default_namespace=DEFAULT_NAMESPACE):
        self.base_kube_client = base_kube_client
        self.client_director = client_director
        self.crd_api_version = crd_api_version
        self.default_namespace = default_namespace

    def create_object(self, object_config, default_namespace=None):
        create_method, is_namespaced, is_custom_object = self.client_director.determine_api_method_for_create_object(self.base_kube_client, object_config.api_version, object_config.kind)
        if default_namespace is None:
            default_namespace = self.default_namespace
        create_args = self.__build_create_arguments(object_config, is_namespaced, default_namespace, is_custom_object)
        create_method(**create_args)

    def read_object(self, api_version, kind, name, namespace=None):
        read_method, is_namespaced, is_custom_object = self.client_director.determine_api_method_for_read_object(self.base_kube_client, api_version, kind)
        if not is_namespaced:
            namespace = None
        elif namespace is None:
            namespace = self.default_namespace
        read_args = self.__build_read_arguments(api_version, kind, name, namespace, is_custom_object)
        return read_method(**read_args)

    def delete_object(self, api_version, kind, name, namespace=None):
        delete_method, is_namespaced, is_custom_object = self.client_director.determine_api_method_for_delete_object(self.base_kube_client, api_version, kind)
        if not is_namespaced:
            namespace = None
        elif namespace is None:
            namespace = self.default_namespace
        delete_args = self.__build_delete_arguments(api_version, kind, name, namespace, is_custom_object)
        delete_method(**delete_args)

    def update_object(self, object_config, default_namespace=None):
        update_method, is_namespaced, is_custom_object = self.client_director.determine_api_method_for_update_object(self.base_kube_client, object_config.api_version, object_config.kind)
        if default_namespace is None:
            default_namespace = self.default_namespace
        update_args = self.__build_update_arguments(object_config, is_namespaced, default_namespace, is_custom_object)
        update_method(**update_args)

    def is_object_namespaced(self, api_version, kind):
        read_method, is_namespaced, is_custom_object = self.client_director.determine_api_method_for_read_object(self.base_kube_client, api_version, kind)
        return is_namespaced

    def __build_create_arguments(self, object_config, is_namespaced, default_namespace, is_custom_object):
        if is_custom_object:
            return self.__build_custom_object_create_arguments(object_config, is_namespaced, default_namespace)
        else:
            return self.__build_builtin_create_arguments(object_config, is_namespaced, default_namespace)

    def __build_builtin_create_arguments(self, object_config, is_namespaced, default_namespace):
        args = {
            'body': object_config.data
        }
        if is_namespaced:
            args['namespace'] = self.__determine_namespace(object_config, default_namespace)
        return args

    def __build_custom_object_create_arguments(self, object_config, is_namespaced, default_namespace):
        group, version = self.client_director.parse_api_version(object_config.api_version)
        plural = self.__determine_custom_object_plural(group, version, object_config.kind)
        args = {
            'group': group,
            'version': version,
            'plural': plural,
            'body': object_config.data
        }
        if is_namespaced:
            args['namespace'] = self.__determine_namespace(object_config, default_namespace)
        return args

    def __build_update_arguments(self, object_config, is_namespaced, default_namespace, is_custom_object):
        if is_custom_object:
            return self.__build_custom_object_update_arguments(object_config, is_namespaced, default_namespace)
        else:
            return self.__build_builtin_update_arguments(object_config, is_namespaced, default_namespace)

    def __build_builtin_update_arguments(self, object_config, is_namespaced, default_namespace):
        args = {
            'body': object_config.data,
            'name': object_config.name
        }
        if is_namespaced:
            args['namespace'] = self.__determine_namespace(object_config, default_namespace)
        return args

    def __build_custom_object_update_arguments(self, object_config, is_namespaced, default_namespace):
        group, version = self.client_director.parse_api_version(object_config.api_version)
        plural = self.__determine_custom_object_plural(group, version, object_config.kind)
        args = {
            'group': group,
            'version': version,
            'plural': plural,
            'body': object_config.data,
            'name': object_config.name
        }
        if is_namespaced:
            args['namespace'] = self.__determine_namespace(object_config, default_namespace)
        return args

    def __build_read_arguments(self, api_version, kind, resource_name, namespace, is_custom_object):
        if is_custom_object:
            return self.__build_custom_object_read_arguments(api_version, kind, resource_name, namespace)
        else:
            return self.__build_builtin_read_arguments(resource_name, namespace)

    def __build_builtin_read_arguments(self, resource_name, namespace):
        args = {
            'name': resource_name
        }
        if namespace is not None:
            args['namespace'] = namespace
        return args

    def __build_custom_object_read_arguments(self, api_version, kind, resource_name, namespace):
        group, version = self.client_director.parse_api_version(api_version)
        plural = self.__determine_custom_object_plural(group, version, kind)
        args = {
            'group': group,
            'version': version,
            'plural': plural,
            'name': resource_name
        }
        if namespace is not None:
            args['namespace'] = namespace
        return args

    def __build_delete_arguments(self, api_version, kind, resource_name, namespace, is_custom_object):
        if is_custom_object:
            return self.__build_custom_object_delete_arguments(api_version, kind, resource_name, namespace)
        else:
            return self.__build_builtin_delete_arguments(resource_name, namespace)

    def __build_builtin_delete_arguments(self, resource_name, namespace):
        args = {
            'name': resource_name
        }
        if namespace is not None:
            args['namespace'] = namespace
        return args

    def __build_custom_object_delete_arguments(self, api_version, kind, resource_name, namespace):
        group, version = self.client_director.parse_api_version(api_version)
        plural = self.__determine_custom_object_plural(group, version, kind)
        args = {
            'group': group,
            'version': version,
            'plural': plural,
            'name': resource_name,
            'body': kubernetes_client_mod.V1DeleteOptions()
        }
        if namespace is not None:
            args['namespace'] = namespace
        return args

    def __determine_custom_object_plural(self, group, version, kind):
        list_method, _, _ = self.client_director.determine_api_method_for_list_object(self.base_kube_client, self.crd_api_version, 'CustomResourceDefinition')
        crds = list_method()
        plural = None
        items = crds if type(crds) == list else crds.items
        for crd in items:
            if crd.spec.group == group and crd.spec.names.kind == kind:
                is_version_match = crd.spec.version == version
                if not is_version_match:
                    crd_versions = crd.spec.versions
                    for crd_version in crd_versions:
                        if crd_version.name == version:
                            is_version_match = True
                            break
                if is_version_match:
                    plural = crd.spec.names.plural
                    break
        if plural is None:
            raise UnrecognisedObjectKindError('Could not find a CRD for custom Resource with group \'{0}\', version \'{1}\', kind \'{2}\' - CRD required to determine the Resource plural'.format(group, version, kind))
        return plural

    def __determine_namespace(self, object_config, default_namespace):
        if 'namespace' in object_config.metadata:
            return object_config.metadata.get('namespace')
        else:
            return default_namespace
