import logging
import tempfile
import base64
import os
import shutil
from kubedriver.keg.model import EntityStates, V1alpha1HelmReleaseStatus, V1alpha1KegCompositionStatus, V1alpha1ObjectStatus
from kubedriver.kegd.model import Tags, Labels, LabelValues, RemoveHelmAction, RemovalTask, RemovalTaskSettings
from kubedriver.keg import CompositionLoader

logger = logging.getLogger(__name__)

class DeployHelmHandler:

    def build_cleanup(self, action, parent_task_settings):
        return RemovalTask(RemovalTaskSettings(), RemoveHelmAction(action.name, namespace=action.namespace))

    def decorate(self, action, parent_task_settings, script_name, keg_name, keg_status):
        helm_status = self.__find_helm_status(action, keg_status)
        self.__do_decorate(helm_status, action, parent_task_settings, script_name, keg_name, keg_status)

    def __do_decorate(self, helm_status, action, parent_task_settings, script_name, keg_name, keg_status):
        if helm_status == None:
            helm_status = V1alpha1HelmReleaseStatus(name=action.name, namespace=action.namespace)
            keg_status.composition.helm_releases.append(helm_status)
            helm_status.state = EntityStates.CREATE_PENDING
        if helm_status.state not in [EntityStates.CREATE_FAILED, EntityStates.CREATE_PENDING]:
            helm_status.state = EntityStates.UPDATE_PENDING
        else:
            helm_status.state = EntityStates.CREATE_PENDING
        helm_status.error = None
        self.__add_tags(helm_status, action.tags, script_name)
        return helm_status

    def handle(self, action, parent_task_settings, script_name, keg_name, keg_status, context, delta_capture, driver_request_id=None):
        helm_client = context.kube_location.helm_client
        task_errors = []
        helm_status = self.__find_helm_status(action, keg_status)
        if helm_status == None:
            helm_status = self.__do_decorate(helm_status, action, parent_task_settings, script_name, keg_name, keg_status)
        tmp_dir = None
        action_type = self.__install_or_upgrade(helm_client, helm_status, driver_request_id=driver_request_id)
        try:
            tmp_dir, chart_path, value_file_paths, setfiles_dict = self.__write_chart(action)
            captured_objects = []
            if action_type == 'Install':
                helm_client.install(chart_path, action.name, action.namespace, values=value_file_paths, setfiles=setfiles_dict, wait=action.wait, timeout=action.timeout, driver_request_id=driver_request_id)
            else:
                captured_objects = self.__pre_capture_objects(context.api_ctl, helm_client, helm_status, driver_request_id=driver_request_id)
                helm_client.upgrade(chart_path, action.name, action.namespace, values=value_file_paths, setfiles=setfiles_dict, reuse_values=True, wait=action.wait, timeout=action.timeout, driver_request_id=driver_request_id)
            helm_status.state = EntityStates.CREATED if action_type == 'Install' else EntityStates.UPDATED
            helm_status.error = None
            self.__capture_deltas(delta_capture, context.api_ctl, helm_client, helm_status, captured_objects, is_upgrade=helm_status.state==EntityStates.UPDATED, driver_request_id=driver_request_id)
        except Exception as e:
            logger.exception(f'{action_type} attempt of helm release \'{action.name}\' in group \'{keg_name}\' failed')
            error_msg = f'{e}'
            task_errors.append(error_msg)
            helm_status.state = EntityStates.CREATE_FAILED if action_type == 'Install' else EntityStates.UPDATE_FAILED
            helm_status.error = error_msg
        finally:
            if tmp_dir is not None and os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)

        return task_errors

    def __install_or_upgrade(self, helm_client, helm_status, driver_request_id=None):
        exists, _ = helm_client.safe_get(helm_status.name, helm_status.namespace, driver_request_id=driver_request_id)
        if exists:
            helm_status.state = EntityStates.UPDATE_PENDING
            return 'Upgrade'
        else:
            helm_status.state = EntityStates.CREATE_PENDING
            return 'Install'

    def __find_helm_status(self, action, keg_status):
        if keg_status.composition != None and keg_status.composition.helm_releases != None:
            for helm_status in keg_status.composition.helm_releases:
                if helm_status.name == action.name and helm_status.namespace == action.namespace:
                    return helm_status
        else:
            keg_status.composition = V1alpha1KegCompositionStatus(helm_releases=[])
        return None

    def __add_tags(self, helm_status, tags, script_name):
        if tags == None:
            tags = {}
        tags[Tags.DEPLOYED_ON] = [script_name]
        if helm_status.tags == None:
            helm_status.tags = {}
        for tag_key, tag_value in tags.items():
            if tag_key not in helm_status.tags:
                helm_status.tags[tag_key] = tag_value
            else:
                if isinstance(tag_value, list):
                    for v in tag_value:
                        if v not in helm_status.tags[tag_key]:
                            helm_status.tags[tag_key].append(v)
                elif tag_value not in helm_status.tags[tag_key]:
                    helm_status.tags[tag_key].append(tag_value)
    
    def __write_chart(self, action):
        tmp_dir = tempfile.mkdtemp()
        if action.chart_encoded == True:
            chart_path = os.path.join(tmp_dir, 'chart.tgz')
            with open(chart_path, 'wb') as writer:
                writer.write(base64.b64decode(action.chart))
        else:
            chart_path = action.chart        

        if action.values != None:
            value_paths = self.__write_value_files(action.values, tmp_dir)
        else:
            value_paths = None

        if action.setfiles != None:
            setfiles_dict = self.__write_set_files(action.setfiles, tmp_dir)
        else:
            setfiles_dict = None

        return tmp_dir, chart_path, value_paths, setfiles_dict

    def __write_value_files(self, data_strings, tmp_dir, file_prefix='values', file_type='yaml'):
        dumped_valuefiles = []
        i = 1
        for data in data_strings:
            filename = file_prefix+'_'+str(i)+'.'+file_type
            filepath = os.path.join(tmp_dir, filename)
            with open(filepath, 'w') as writer:
                writer.write(data)
            i += 1
            dumped_valuefiles.append(filepath)
        return dumped_valuefiles

    def __write_set_files(self, setfiles, tmp_dir):
        dumped_setfiles = {}
        for key in setfiles:
            # setfiles can be arbitrary text files so just use a generic name here
            filename = key+'_setfile.data'
            filepath = os.path.join(tmp_dir, filename)
            with open(filepath, 'w') as writer:
                writer.write(setfiles[key])
            dumped_setfiles[key] = filepath
        return dumped_setfiles

    def __pre_capture_objects(self, api_ctl, helm_client, helm_status, driver_request_id=None):
        helm_release_details = helm_client.get(helm_status.name, helm_status.namespace, driver_request_id=driver_request_id)
        loader = CompositionLoader(api_ctl, helm_client)
        loaded_objects = loader.load_objects_in_helm_release(helm_release_details)
        return loaded_objects

    def __capture_deltas(self, delta_capture, api_ctl, helm_client, helm_status, pre_captured_objects, is_upgrade, driver_request_id=None):
        helm_release_details = helm_client.get(helm_status.name, helm_status.namespace, driver_request_id=driver_request_id)
        loader = CompositionLoader(api_ctl, helm_client)
        loaded_objects = loader.load_objects_in_helm_release(helm_release_details)
        objects_only = False
        if is_upgrade:
            deployed_objects, removed_objects = self.__delta_snapshot_of_lists(pre_captured_objects, loaded_objects)
            if len(deployed_objects) + len(removed_objects) == 0:
                # If no objects changed, don't include the Helm release on the delta
                return 
            objects_only = True
            deployed_objects = [self.__dict_to_obj_status(obj) for obj in deployed_objects]
            removed_objects = [self.__dict_to_obj_status(obj) for obj in removed_objects]
        else:
            removed_objects = None
            deployed_objects = [self.__dict_to_obj_status(obj) for obj in loaded_objects]
        delta_capture.deployed_helm_release(helm_status, objects_only=objects_only, deployed_objects=deployed_objects, removed_objects=removed_objects)

    def __delta_snapshot_of_lists(self, before, after):
        removed = []
        added = []
        for item in (before + after):
            existed_before = self.__find_obj_in_list(item, before)
            existed_after = self.__find_obj_in_list(item, after)
            if existed_before and not existed_after:
                removed.append(item)
            elif not existed_before and existed_after:
                added.append(item)
        return added, removed

    def __find_obj_in_list(self, obj_dict, the_list):
        for item in the_list:
            if item.get('apiVersion') == obj_dict.get('apiVersion') and item.get('kind') == obj_dict.get('kind'):
                item_meta = item.get('metadata')
                obj_meta = obj_dict.get('metadata')
                if (item_meta != None and obj_meta != None and item_meta.get('name') == obj_meta.get('name') 
                        and item_meta.get('namespace') == obj_meta.get('namespace')):
                        return True
        return False

    def __dict_to_obj_status(self, obj_dict):
        group = obj_dict.get('apiVersion')
        kind = obj_dict.get('kind')
        metadata = obj_dict.get('metadata')
        name = metadata.get('name')
        namespace = metadata.get('namespace')
        uid = metadata.get('uid')
        return V1alpha1ObjectStatus(group=group, kind=kind, name=name, namespace=namespace, uid=uid)
