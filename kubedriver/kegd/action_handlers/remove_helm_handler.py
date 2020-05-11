import logging
from kubernetes.client.rest import ApiException
from kubedriver.keg.model import EntityStates, V1alpha1HelmReleaseStatus, V1alpha1KegCompositionStatus

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

    def handle(self, action, parent_task_settings, script_name, keg_name, keg_status, context):
        helm_client = context.kube_location.helm_client
        task_errors = []
        helm_status = self.__find_helm_status(action, keg_status)

        try:
            helm_client.get(action.name)
            # Found
            should_delete = True
        except Exception as e:
            should_delete = False
            if f'release: \"{action.name}\" not found' in str(e):
                #Not found, so ignore the delete
                pass
            else:
                logger.exception(f'Checking existence of helm release \'{action.name}\' in group \'{keg_name}\' failed')
                error_msg = str(e)
                task_errors.append(error_msg)
                helm_status.state = EntityStates.DELETE_FAILED
                helm_status.error = error_msg
        if should_delete:
            try:
                helm_client.purge(action.name)
                helm_status.state = EntityStates.DELETED
                helm_status.error = None
            except Exception as e:
                logger.exception(f'Delete attempt of helm release \'{action.name}\' in group \'{keg_name}\' failed')
                error_msg = str(e)
                task_errors.append(error_msg)
                helm_status.state = EntityStates.DELETE_FAILED
                helm_status.error = error_msg
        return task_errors

    def __find_helm_status(self, action, keg_status):
        if keg_status.composition != None and keg_status.composition.helm_releases != None:
            for helm_status in keg_status.composition.helm_releases:
                if helm_status.name == action.name and helm_status.namespace == action.namespace:
                    return helm_status
        else:
            keg_status.composition = V1alpha1KegCompositionStatus(helm_releases=[])
        return None