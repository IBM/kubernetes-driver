import logging
from kubedriver.keg.model import EntityStates, V1alpha1ObjectStatus, V1alpha1KegCompositionStatus
from kubedriver.kegd.model import Tags, Labels, LabelValues, RemoveObjectAction, RemovalTask, RemovalTaskSettings
from kubedriver.kubeclient import ErrorReader
from kubedriver.kubeobjects import ObjectConfiguration, ObjectConfigUtils

logger = logging.getLogger(__name__)

class DeployObjectHandler:

    def __init__(self):
        self.error_reader = ErrorReader()
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
        else:
            obj_status.state = EntityStates.UPDATE_PENDING
        obj_status.error = None
        self.__add_tags(obj_status, action.tags, script_name)

    def handle(self, action, parent_task_settings, script_name, keg_name, keg_status, context):
        api_ctl = context.api_ctl
        task_errors = []
        obj_status = self.__find_object(action, keg_status)
        if obj_status == None:
            self.__do_decorate(obj_status, action, parent_task_settings, script_name, keg_name, keg_status)
        object_config = ObjectConfiguration(action.config)
        self.config_utils.add_label(object_config, Labels.MANAGED_BY, LabelValues.MANAGED_BY)
        self.config_utils.add_label(object_config, Labels.KEG, keg_name)
        try:
            if obj_status.state == EntityStates.UPDATE_PENDING:
                api_ctl.update_object(object_config)
            else:
                api_ctl.create_object(object_config)
            obj_status.state = EntityStates.CREATED
            obj_status.error = None
        except Exception as e:
            logger.exception(f'Create attempt of object ({object_config.reference}) in group \'{keg_name}\' failed')
            if self.error_reader.is_api_exception(e):
                error_msg = self.error_reader.summarise_error(e)
            else:
                error_msg = str(e)
            task_errors.append(error_msg)
            obj_status.state = EntityStates.CREATE_FAILED
            obj_status.error = error_msg
        return task_errors

    def build_cleanup(self, action, parent_task_settings):
        return RemovalTask(RemovalTaskSettings(), RemoveObjectAction(action.group, action.kind, action.name, namespace=action.namespace))

    def __check_exists(self, keg_name, api_ctl, object_config):
        try:
            existing = api_ctl.read_object(object_config.api_version, object_config.kind, object_config.name, namespace=object_config.namespace)
            return None, True
        except Exception as e:
            if self.error_reader.is_not_found_err(e):
                return None, False
            else:
                logger.exception(f'Checking existence of object ({object_config.reference}) in group \'{keg_name}\' failed')
                return None, e

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
    