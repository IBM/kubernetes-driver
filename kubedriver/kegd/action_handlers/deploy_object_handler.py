import logging
from kubedriver.keg.model import EntityStates, V1alpha1ObjectStatus
from kubedriver.kegd.model import Tags, Labels, LabelValues
from kubedriver.kubeclient import ErrorReader
from kubedriver.kubeobjects import ObjectConfiguration, ObjectConfigUtils

logger = logging.getLogger(__name__)

class DeployObjectHandler:

    def __init__(self):
        self.error_reader = ErrorReader()
        self.config_utils = ObjectConfigUtils()

    def decorate(self, action, parent_task_settings, operation_exec_name, keg_name, keg_status):
        obj_status = self.__find_object(action, keg_status)
        self.__do_decorate(obj_status, action, parent_task_settings, operation_exec_name, keg_name, keg_status)

    def __do_decorate(self, obj_status, action, parent_task_settings, operation_exec_name, keg_name, keg_status):
        if obj_status == None:
            obj_status = V1alpha1ObjectStatus(group=action.group, kind=action.kind, namespace=action.namespace, 
                                                name=action.name)
            keg_status.composition.objects.append(obj_status)
        obj_status.state = EntityStates.CREATE_PENDING
        obj_status.error = None
        self.__add_tags(obj_status, action.tags, operation_exec_name)

    def handle(self, action, parent_task_settings, operation_exec_name, keg_name, keg_status, api_ctl):
        task_errors = []
        obj_status = self.__find_object(action, keg_status)
        if obj_status == None:
            self.__do_decorate(obj_status, action, parent_task_settings, operation_exec_name, keg_name, keg_status)
        object_config = ObjectConfiguration(action.config)
        self.config_utils.add_label(object_config, Labels.MANAGED_BY, LabelValues.MANAGED_BY)
        self.config_utils.add_label(object_config, Labels.KEG, keg_name)
        try:
            api_ctl.create_object(object_config)
            obj_status.state = EntityStates.CREATED
            obj_status.error = None
        except Exception as e:
            logger.exception(f'Create attempt of object ({object_config.reference}) in group \'{keg_name}\' failed')
            error_msg = str(e)
            task_errors.append(error_msg)
            obj_status.state = EntityStates.CREATE_FAILED
            obj_status.error = error_msg
        return task_errors
        
    def __find_object(self, action, keg_status):
        for obj_status in keg_status.composition.objects:
            if (obj_status.group == action.group and obj_status.kind == action.kind 
            and obj_status.name == action.name and obj_status.namespace == action.namespace):
                return obj_status
        return None
     
    def __add_tags(self, obj_status, tags, operation_exec_name):
        if tags == None:
            tags = {}
        tags[Tags.DEPLOYED_ON] = [operation_exec_name]
        if obj_status.tags == None:
            obj_status.tags = {}
        for tag_key, tag_value in tags.items():
            if tag_key not in obj_status.tags:
                obj_status.tags[tag_key] = tag_value
            else:
                obj_status.tags[tag_key].append(tag_value)
    