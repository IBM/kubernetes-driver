import logging
from .defaults import DEFAULT_NAMESPACE
from openshift.dynamic.exceptions import NotFoundError
from openshift.dynamic import DynamicClient
from kubernetes.client import V1DeleteOptions

logger = logging.getLogger(__name__)

class OpenshiftApiController:

    def __init__(self, base_kube_client, default_namespace=DEFAULT_NAMESPACE):
        self.base_kube_client = base_kube_client
        self.dynamic_client = DynamicClient(base_kube_client)
        self.default_namespace = default_namespace

    def __get_resource_client(self, api_version, kind):
        return self.dynamic_client.resources.get(api_version=api_version, kind=kind)
    
    def create_object(self, object_config, default_namespace=None):
        resource_client = self.__get_resource_client(object_config.api_version, object_config.kind)
        create_args = self.__build_create_arguments(resource_client, object_config, default_namespace)
        return resource_client.create(**create_args)

    def __build_create_arguments(self, resource_client, object_config, supplied_default_namespace):
        args = {
            'body': object_config.data
        }
        if resource_client.namespaced:
            args['namespace'] = self.__determine_namespace(object_config, supplied_default_namespace)
        return args

    def update_object(self, object_config, default_namespace=None, resource_version=None):
        logger.debug(f'update_object1 object_config={object_config}')
        resource_client = self.__get_resource_client(object_config.api_version, object_config.kind)
        if resource_version is not None:
            metadata = object_config.data.get('metadata', {})
            metadata['resourceVersion'] = resource_version
        update_args = self.__build_update_arguments(resource_client, object_config, default_namespace)
        logger.debug(f'update_object2 update_args={update_args}')
        return resource_client.replace(**update_args)

    def __build_update_arguments(self, resource_client, object_config, supplied_default_namespace):
        args = {
            'body': object_config.data
        }
        if resource_client.namespaced:
            args['namespace'] = self.__determine_namespace(object_config, supplied_default_namespace)
        return args

    def safe_read_object(self, api_version, kind, name, namespace=None):
        try:
            obj = self.read_object(api_version, kind, name, namespace=namespace)
            return True, obj
        except NotFoundError:
            return False, None

    def read_object(self, api_version, kind, name, namespace=None):
        resource_client = self.__get_resource_client(api_version, kind)
        read_args = self.__build_read_arguments(resource_client, name, namespace)
        return resource_client.get(**read_args)

    def __build_read_arguments(self, resource_client, name, namespace):
        args = {
            'name': name
        }
        if namespace is not None:
            args['namespace'] = namespace
        return args

    def delete_object(self, api_version, kind, name, namespace=None):
        resource_client = self.__get_resource_client(api_version, kind)
        delete_args = self.__build_delete_arguments(resource_client, name, namespace)
        resource_client.delete(**delete_args)

    def __build_delete_arguments(self, resource_client, name, namespace):
        args = {
            'name': name,
            'body': V1DeleteOptions()
        }
        if namespace is not None:
            args['namespace'] = namespace
        return args

    def is_object_namespaced(self, api_version, kind):
        resource_client = self.__get_resource_client(api_version, kind)
        return resource_client.namespaced

    def __determine_namespace(self, object_config, supplied_default_namespace):
        if 'namespace' in object_config.metadata:
            return object_config.metadata.get('namespace')
        elif supplied_default_namespace is not None:
            return supplied_default_namespace
        else:
            return self.default_namespace

    def watch(self):
        w = watch.Watch()
        for event in w.stream(v1.list_pod_for_all_namespaces):
            print("Event: %s %s %s" % (event['type'], event['object'].kind, event['object'].metadata.name))

        watch = kubernetes.watch.Watch()
        core_v1 = k8s.CoreV1Api()
        for event in watch.stream(func=core_v1.list_namespaced_pod,
                                namespace=namespace,
                                label_selector=label,
                                timeout_seconds=60):
            if event["object"].status.phase == "Running":
                watch.stop()
                end_time = time.time()
                logger.info("%s started in %0.2f sec", full_name, end_time-start_time)
                return
            # event.type: ADDED, MODIFIED, DELETED
            if event["type"] == "DELETED":
                # Pod was deleted while we were waiting for it to start.
                logger.debug("%s deleted before it started", full_name)
                watch.stop()
                return