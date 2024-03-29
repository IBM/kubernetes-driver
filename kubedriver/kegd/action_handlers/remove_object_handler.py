import logging
from kubernetes.client.rest import ApiException
from kubedriver.keg.model import EntityStates, V1alpha1ObjectStatus, V1alpha1KegCompositionStatus
from kubedriver.kubeobjects import ObjectReference
from openshift.dynamic.exceptions import NotFoundError, DynamicApiError

logger = logging.getLogger(__name__)

class RemoveObjectHandler:

    def __init__(self):
        pass

    def decorate(self, action, parent_task_settings, script_name, keg_name, keg_status):
        obj_status = self.__find_object(action, keg_status)
        self.__do_decorate(obj_status, action, parent_task_settings, script_name, keg_name, keg_status)

    def __do_decorate(self, obj_status, action, parent_task_settings, script_name, keg_name, keg_status):
        if obj_status == None:
            obj_status = V1alpha1ObjectStatus(group=action.group, kind=action.kind, namespace=action.namespace, 
                                                name=action.name)
            keg_status.composition.objects.append(obj_status)
        obj_status.state = EntityStates.DELETE_PENDING
        obj_status.error = None

    def handle(self, action, parent_task_settings, script_name, keg_name, keg_status, context, delta_capture, driver_request_id=None):
        api_ctl = context.api_ctl
        task_errors = []
        obj_status = self.__find_object(action, keg_status)
        if obj_status != None:
            try:
                api_ctl.delete_object(action.group, action.kind, action.name, namespace=action.namespace, driver_request_id=driver_request_id)
                obj_status.state = EntityStates.DELETED
                obj_status.error = None
            except NotFoundError:
                # Object not found, assume it is already deleted
                obj_status.state = EntityStates.DELETED
                obj_status.error = None
            except Exception as e:
                reference = ObjectReference(action.group, action.kind, action.name, namespace=action.namespace)
                logger.exception(f'Delete attempt of object ({reference}) in group \'{keg_name}\' failed')
                if isinstance(e, DynamicApiError):
                    error_msg = e.summary()
                else:
                    error_msg = f'{e}'
                task_errors.append(error_msg)
                obj_status.state = EntityStates.DELETE_FAILED
                obj_status.error = error_msg
            if obj_status.state == EntityStates.DELETED:
                self.__capture_deltas(delta_capture, obj_status)
                self.__remove_object_from_composition(action, keg_status)
        return task_errors

    def __find_object(self, action, keg_status):
        if keg_status.composition != None and keg_status.composition.objects != None:
            for obj_status in keg_status.composition.objects:
                if (obj_status.group == action.group and obj_status.kind == action.kind 
                and obj_status.name == action.name and obj_status.namespace == action.namespace):
                    return obj_status
        else:
            keg_status.composition = V1alpha1KegCompositionStatus(objects=[])
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

    def __capture_deltas(self, delta_capture, object_status):
        delta_capture.removed_object(object_status)