import logging
from kubernetes.client.rest import ApiException
from kubedriver.keg.model import EntityStates,V1alpha1ObjectStatus
from kubedriver.kubeobjects import ObjectReference
from kubedriver.kubeclient import ErrorReader

logger = logging.getLogger(__name__)

class WithdrawObjectHandler:

    def __init__(self):
        self.error_reader = ErrorReader()

    def decorate(self, action, parent_task_settings, operation_exec_name, keg_name, keg_status):
        obj_status = self.__find_object(action, keg_status)
        self.__do_decorate(obj_status, action, parent_task_settings, operation_exec_name, keg_name, keg_status)

    def __do_decorate(self, obj_status, action, parent_task_settings, operation_exec_name, keg_name, keg_status):
        if obj_status == None:
            obj_status = V1alpha1ObjectStatus(group=action.group, kind=action.kind, namespace=action.namespace, 
                                                name=action.name)
            keg_status.composition.objects.append(obj_status)
        obj_status.state = EntityStates.DELETE_PENDING
        obj_status.error = None

    def handle(self, action, parent_task_settings, operation_exec_name, keg_name, keg_status, api_ctl):
        task_errors = []
        obj_status = self.__find_object(action, keg_status)
        try:
            api_ctl.delete_object(action.group, action.kind, action.name, namespace=action.namespace)
            obj_status.state = EntityStates.DELETED
            obj_status.error = None
        except Exception as e:
            if isinstance(e, ApiException) and self.error_reader.is_not_found_err(e):
                # Object not found, assume it is already delete
                obj_status.state = EntityStates.DELETED
                obj_status.error = None
            else:
                reference = ObjectReference(action.group, action.kind, action.name, namespace=action.namespace)
                logger.exception(f'Delete attempt of object ({reference}) in group \'{keg_name}\' failed')
                error_msg = str(e)
                task_errors.append(error_msg)
                obj_status.state = EntityStates.DELETE_FAILED
                obj_status.error = error_msg
        if obj_status.state == EntityStates.DELETED:
            self.__remove_object_from_composition(action, keg_status)
        return task_errors

    def __find_object(self, action, keg_status):
        for obj_status in keg_status.composition.objects:
            if (obj_status.group == action.group and obj_status.kind == action.kind 
            and obj_status.name == action.name and obj_status.namespace == action.namespace):
                return obj_status
        return None

    def __remove_object_from_composition(self, action, keg_status):
        new_objects = []
        for obj_status in keg_status.composition.objects:
            if (obj_status.group == action.group and obj_status.kind == action.kind 
            and obj_status.name == action.name and obj_status.namespace == action.namespace):
                pass
            else:
                new_objects.append(obj_status)
        keg_status.composition.objects = new_objects