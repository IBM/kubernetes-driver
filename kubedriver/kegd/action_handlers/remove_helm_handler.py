import logging
from kubernetes.client.rest import ApiException
from kubedriver.keg.model import EntityStates, V1alpha1HelmReleaseStatus, V1alpha1KegCompositionStatus, V1alpha1ObjectStatus
from kubedriver.keg import CompositionLoader

logger = logging.getLogger(__name__)

class RemoveHelmHandler:

    def decorate(self, action, parent_task_settings, script_name, keg_name, keg_status):
        helm_status = self.__find_helm_status(action, keg_status)
        self.__do_decorate(helm_status, action, parent_task_settings, script_name, keg_name, keg_status)

    def __do_decorate(self, helm_status, action, parent_task_settings, script_name, keg_name, keg_status):
        if helm_status == None:
            helm_status = V1alpha1HelmReleaseStatus(namespace=action.namespace, name=action.name)
            keg_status.composition.helm_releases.append(helm_status)
        helm_status.state = EntityStates.DELETE_PENDING
        helm_status.error = None

    def handle(self, action, parent_task_settings, script_name, keg_name, keg_status, context, delta_capture):
        helm_client = context.kube_location.helm_client
        task_errors = []
        helm_status = self.__find_helm_status(action, keg_status)
        if helm_status != None:
            should_delete = False
            try:
                found, _ = helm_client.safe_get(action.name, action.namespace)
                if found: 
                    should_delete = True
            except Exception as e:
                logger.exception(f'Checking existence of helm release \'{action.name}\' in group \'{keg_name}\' failed')
                error_msg = f'{e}'
                task_errors.append(error_msg)
                helm_status.state = EntityStates.DELETE_FAILED
                helm_status.error = error_msg

            if len(task_errors) == 0:
                if should_delete:
                    try:
                        captured_objects = self.__pre_capture_objects(context.api_ctl, helm_client, helm_status)
                        helm_client.purge(action.name, action.namespace)
                        helm_status.state = EntityStates.DELETED
                        helm_status.error = None
                        self.__capture_deltas(delta_capture, helm_status, captured_objects)
                    except Exception as e:
                        logger.exception(f'Delete attempt of helm release \'{action.name}\' in group \'{keg_name}\' failed')
                        error_msg = f'{e}'
                        task_errors.append(error_msg)
                        helm_status.state = EntityStates.DELETE_FAILED
                        helm_status.error = error_msg

                if helm_status.state == EntityStates.DELETED:
                    self.__remove_helm_release_from_composition(action, keg_status)

        return task_errors

    def __find_helm_status(self, action, keg_status):
        if keg_status.composition != None and keg_status.composition.helm_releases != None:
            for helm_status in keg_status.composition.helm_releases:
                if helm_status.name == action.name and helm_status.namespace == action.namespace:
                    return helm_status
        else:
            keg_status.composition = V1alpha1KegCompositionStatus(helm_releases=[])
        return None

    def __remove_helm_release_from_composition(self, action, keg_status):
        new_helm_releases = []
        for helm_status in keg_status.composition.helm_releases:
            if helm_status.name == action.name and helm_status.namespace == action.namespace:
                pass
            else:
                new_helm_releases.append(helm_status)
        keg_status.composition.helm_releases = new_helm_releases

    def __pre_capture_objects(self, api_ctl, helm_client, helm_status):
        helm_release_details = helm_client.get(helm_status.name, helm_status.namespace)
        loader = CompositionLoader(api_ctl, helm_client)
        loaded_objects = loader.load_objects_in_helm_release(helm_release_details)
        return loaded_objects

    def __capture_deltas(self, delta_capture, helm_status, captured_objects):
        removed_objects = [self.__dict_to_obj_status(obj) for obj in captured_objects]
        delta_capture.removed_helm_release(helm_status, removed_objects=removed_objects)

    def __dict_to_obj_status(self, obj_dict):
        group = obj_dict.get('apiVersion')
        kind = obj_dict.get('kind')
        metadata = obj_dict.get('metadata')
        name = metadata.get('name')
        namespace = metadata.get('namespace')
        return V1alpha1ObjectStatus(group=group, kind=kind, name=name, namespace=namespace)