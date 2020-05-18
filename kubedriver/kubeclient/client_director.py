import kubernetes.client as kubernetes_client_mod
from .exceptions import ClientMethodNotFoundError
from .mod_director import ModDirector
from .crd_director import CrdDirector

CUSTOM_OBJECT_KIND = 'CustomObject'

class KubeClientDirector:

    def __init__(self, base_kube_client):
        self.base_kube_client = base_kube_client
        self.mod_director = KubeModDirector()

    def determine_api_method_for_create_object(self, api_version, kind, return_api_client=False):
        return self.__determine_api_method_for_action(api_version, kind, CREATE_ACTION, return_api_client)
    
    def determine_api_method_for_update_object(self, api_version, kind, return_api_client=False):
        return self.__determine_api_method_for_action(api_version, kind, UPDATE_ACTION, return_api_client)
    
    def determine_api_method_for_delete_object(self, api_version, kind, return_api_client=False):
        return self.__determine_api_method_for_action(api_version, kind, DELETE_ACTION, return_api_client)
    
    def determine_api_method_for_read_object(self, api_version, kind, return_api_client=False):
        return self.__determine_api_method_for_action(api_version, kind, READ_ACTION, return_api_client)
    
    def determine_api_method_for_list_object(self, api_version, kind, return_api_client=False):
        return self.__determine_api_method_for_action(api_version, kind, LIST_ACTION, return_api_client)

    def __determine_api_method_for_action(self, api_version, kind, action_type, return_api_client):
        api_client = self.mod_director.build_api_client_for_version(api_version, self.base_kube_client)
        method, is_namespaced, is_custom_object = self.__find_api_method(api_client, kind, action_type)
        if return_api_client:
            return method, is_namespaced, is_custom_object, api_client
        else:
            return method, is_namespaced, is_custom_object

    def __find_api_method(self, api_client, kind, action_type):
        if api_client.__class__ == kubernetes_client_mod.CustomObjectsApi:
            method, is_namespaced = self.__find_custom_object_api_method(api_client, kind, action_type)
            return method, is_namespaced, True
        else:
            method, is_namespaced = self.__find_builtin_api_method(api_client, kind, action_type)
            return method, is_namespaced, False

    def __find_builtin_api_method(self, api_client, kind, action_type):
        is_namespaced, method = self.try_namespaced_method(api_client, action_type, kind)
        if not is_namespaced:
            is_plain, method = self.try_plain_method(api_client, action_type, kind)
            if not is_plain:
                raise ClientMethodNotFoundError(f'Cannot determine method for action \'{action_type}\' of kind \'{kind}\' in Api client \'{api_client.__class__}\'')
        return method, is_namespaced

    def __find_custom_object_api_method(self, api_client, kind, action_type):
        self.crd_director.get_crd(kind)
        if action_type == READ_ACTION:
            action_type = GET_ACTION #custom objects have a different verb
        is_namespaced, method = self.try_namespaced_method(api_client, action_type, CUSTOM_OBJECT_KIND)
        if not is_namespaced:
            raise ClientMethodNotFoundError(f'Cannot determine method for action \'{action_type}\' of custom object kind \'{kind}\' in Api client \'{api_client.__class__}\'')
        return method, is_namespaced
