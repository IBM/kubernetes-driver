import logging
from kubedriver.keg.model import EntityStates, V1alpha1ObjectStatus, V1alpha1KegCompositionStatus
from kubedriver.kegd.model import Tags, Labels, LabelValues, RemoveObjectAction, RemovalTask, RemovalTaskSettings
from kubedriver.kubeobjects import ObjectConfiguration, ObjectConfigUtils
from openshift.dynamic.exceptions import DynamicApiError

logger = logging.getLogger(__name__)

class DeployObjectHandler:

    def __init__(self):
        self.config_utils = ObjectConfigUtils()

    def decorate(self, action, parent_task_settings, script_name, keg_name, keg_status):
        obj_status = self.__find_object(action, keg_status)
        self.__do_decorate(obj_status, action, parent_task_settings, script_name, keg_name, keg_status)

    def __do_decorate(self, obj_status, action, parent_task_settings, script_name, keg_name, keg_status):
        if obj_status == None:
            obj_status = V1alpha1ObjectStatus(group=action.group, kind=action.kind, namespace=action.namespace, 
                                                name=action.name)
            keg_status.composition.objects.append(obj_status)
            obj_status.state = EntityStates.CREATE_PENDING
        if obj_status.state not in [EntityStates.CREATE_FAILED, EntityStates.CREATE_PENDING]:
            obj_status.state = EntityStates.UPDATE_PENDING
        else:
            obj_status.state = EntityStates.CREATE_PENDING
        obj_status.error = None
        self.__add_tags(obj_status, action.tags, script_name)
        return obj_status

    def handle(self, action, parent_task_settings, script_name, keg_name, keg_status, context, delta_capture, driver_request_id=None):
        api_ctl = context.api_ctl
        task_errors = []
        obj_status = self.__find_object(action, keg_status)
        if obj_status == None:
            obj_status = self.__do_decorate(obj_status, action, parent_task_settings, script_name, keg_name, keg_status)
        object_config = ObjectConfiguration(action.config)
        self.config_utils.add_label(object_config, Labels.MANAGED_BY, LabelValues.MANAGED_BY)
        self.config_utils.add_label(object_config, Labels.KEG, keg_name)
        try:
            # logger.info("!!!object_config %s", object_config)
            if obj_status.state == EntityStates.UPDATE_PENDING:
                return_obj = api_ctl.update_object(object_config, driver_request_id=driver_request_id)
            else:
                return_obj = api_ctl.create_object(object_config, driver_request_id=driver_request_id)
            obj_status.uid = self.__get_uid(return_obj)
            obj_status.state = EntityStates.CREATED if obj_status.state == EntityStates.CREATE_PENDING else EntityStates.UPDATED
            obj_status.error = None
            if obj_status.state == EntityStates.CREATED:
                self.__capture_deltas(delta_capture, obj_status)
        except Exception as e:
            logger.exception(f'Create attempt of object ({object_config.reference}) in group \'{keg_name}\' failed')
            if isinstance(e, DynamicApiError):
                error_msg = e.summary()
            else:
                error_msg = f'{e}'
            task_errors.append(error_msg)
            obj_status.state = EntityStates.CREATE_FAILED if obj_status.state == EntityStates.CREATE_PENDING else EntityStates.UPDATE_FAILED
            obj_status.error = error_msg
        return task_errors

    def __get_uid(self, return_obj):
        if hasattr(return_obj, 'metadata'):
            metadata = return_obj.metadata
            return metadata.uid
        else:
            metadata = return_obj.get('metadata', {})
            return metadata.get('uid')

    def build_cleanup(self, action, parent_task_settings):
        return RemovalTask(RemovalTaskSettings(), RemoveObjectAction(action.group, action.kind, action.name, namespace=action.namespace))

    def __find_object(self, action, keg_status):
        if keg_status.composition != None and keg_status.composition.objects != None:
            for obj_status in keg_status.composition.objects:
                if (obj_status.group == action.group and obj_status.kind == action.kind 
                and obj_status.name == action.name and obj_status.namespace == action.namespace):
                    return obj_status
        else:
            keg_status.composition = V1alpha1KegCompositionStatus(objects=[])
        return None
     
    def __add_tags(self, obj_status, tags, script_name):
        if tags == None:
            tags = {}
        tags[Tags.DEPLOYED_ON] = [script_name]
        if obj_status.tags == None:
            obj_status.tags = {}
        for tag_key, tag_value in tags.items():
            if tag_key not in obj_status.tags:
                obj_status.tags[tag_key] = tag_value
            else:
                if isinstance(tag_value, list):
                    for v in tag_value:
                        if v not in obj_status.tags[tag_key]:
                            obj_status.tags[tag_key].append(v)
                elif tag_value not in obj_status.tags[tag_key]:
                    obj_status.tags[tag_key].append(tag_value)
    
    def __capture_deltas(self, delta_capture, object_status):
        delta_capture.deployed_object(object_status)