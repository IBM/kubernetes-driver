import logging
import tempfile
import base64
import os
import shutil
from kubedriver.keg.model import EntityStates, V1alpha1HelmReleaseStatus, V1alpha1KegCompositionStatus
from kubedriver.kegd.model import Tags, Labels, LabelValues

logger = logging.getLogger(__name__)

class DeployHelmHandler:

    def decorate(self, action, parent_task_settings, script_name, keg_name, keg_status):
        helm_status = self.__find_helm_status(action, keg_status)
        self.__do_decorate(helm_status, action, parent_task_settings, script_name, keg_name, keg_status)

    def __do_decorate(self, helm_status, action, parent_task_settings, script_name, keg_name, keg_status):
        if helm_status == None:
            helm_status = V1alpha1HelmReleaseStatus(namespace=action.namespace, name=action.name)
            keg_status.composition.helm_releases.append(helm_status)
        helm_status.state = EntityStates.CREATE_PENDING
        helm_status.error = None
        self.__add_tags(helm_status, action.tags, script_name)

    def handle(self, action, parent_task_settings, script_name, keg_name, keg_status, context):
        helm_client = context.kube_location.helm_client
        task_errors = []
        helm_status = self.__find_helm_status(action, keg_status)
        if helm_status == None:
            self.__do_decorate(helm_status, action, parent_task_settings, script_name, keg_name, keg_status)
        
        try:
            helm_client.get(action.name)
            # Found
            must_recreate = True
        except Exception as e:
            must_recreate = False
            if f'release: \"{action.name}\" not found' in str(e):
                #Not found, so can create freely
                pass
            else:
                logger.exception(f'Checking existence of helm release \'{action.name}\' in group \'{keg_name}\' failed')
                error_msg = str(e)
                task_errors.append(error_msg)
                helm_status.state = EntityStates.CREATE_FAILED
                helm_status.error = error_msg

        if must_recreate is True:
            try:
                helm_client.purge(action.name)
            except Exception as e:
                logger.exception(f'Attempting to recreate helm release \'{action.name}\' in group \'{keg_name}\' failed')
                error_msg = str(e)
                task_errors.append(error_msg)
                helm_status.state = EntityStates.CREATE_FAILED
                helm_status.error = error_msg

        if len(task_errors) == 0:
            tmp_dir = None
            try:
                tmp_dir, chart_path, values_path = self.__write_chart(action)
                helm_client.install(chart_path, action.name, action.namespace, values=values_path)
                helm_status.state = EntityStates.CREATED
                helm_status.error = None
            except Exception as e:
                logger.exception(f'Create attempt of helm release \'{action.name}\' in group \'{keg_name}\' failed')
                error_msg = str(e)
                task_errors.append(error_msg)
                helm_status.state = EntityStates.CREATE_FAILED
                helm_status.error = error_msg
            finally:
                if tmp_dir is not None and os.path.exists(tmp_dir):
                    shutil.rmtree(tmp_dir)

        return task_errors

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
            values_path = os.path.join(tmp_dir, 'values.yaml')
            with open(values_path, 'w') as writer:
                writer.write(action.values)
        else:
            values_path = None
        return tmp_dir, chart_path, values_path

    def __write_values(self, values_string):
        tmp_dir = tempfile.mkdtemp()
        values_path = os.path.join(tmp_dir, 'values.yaml')
        with open(values_path, 'w') as writer:
            writer.write(values_string)
        return values_path, tmp_dir