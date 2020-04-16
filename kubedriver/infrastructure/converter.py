import tempfile
import yaml
import base64
import os
from ignition.service.framework import Service, Capability
from ignition.service.infrastructure import InvalidInfrastructureTemplateError, InvalidInfrastructureRequestError
from .template_types import TemplateTypes
from .name_manager import NameManager
from kubedriver.helmobjects import HelmReleaseConfiguration
from kubedriver.kubeobjects import ObjectConfigurationDocument
from kubedriver.kubegroup import EntityGroup

name_manager = NameManager()

class InfrastructureConverter(Service, Capability):

    def __init__(self, templating, template_context_builder):
        self.templating = templating
        self.template_context_builder = template_context_builder
    
    def convert_to_entity_group(self, template, template_type, system_properties, properties, kube_location):
        objects = []
        helm_releases = []
        if TemplateTypes.is_helm(template_type):
            helm_releases.append(self.__render_template_to_helm_release(template, system_properties, properties, kube_location))
        elif TemplateTypes.is_object_configuration(template_type):
            objects = self.__render_template_to_object_configurations(template, system_properties, properties, kube_location)
        else:
            raise InvalidInfrastructureTemplateError(f'Template type must be one of {TemplateTypes.describe_possible_values()} but was \'{template_type}\'')
        uid = self.__generate_group_uid(system_properties)
        return EntityGroup(uid, objects=objects, helm_releases=helm_releases)
            
    def __generate_group_uid(self, system_properties):
        resource_id = system_properties.get('resourceId', None)
        if resource_id == None:
            raise InvalidInfrastructureRequestError('system properties missing \'resourceId\' value')
        resource_name = system_properties.get('resourceName', None)
        if resource_name == None:
            raise InvalidInfrastructureRequestError('system properties missing \'resourceName\' value')
        return name_manager.safe_subdomain_name_for_resource(resource_id, resource_name)

    def __render_template_to_object_configurations(self, template, system_properties, properties, kube_location):
        render_context = self.template_context_builder.build(system_properties, properties, kube_location.to_dict())
        rendered_template = self.templating.render(template, render_context)
        return ObjectConfigurationDocument(rendered_template).read()

    def __render_template_to_helm_release(self, template, system_properties, properties, kube_location):
        chart_path, values_path = self.__write_helm_template_to_disk(template)
        self.__render_helm_values_template(values_path, system_properties, properties, kube_location)
        release_name = self.__generate_helm_release_name(system_properties)
        install_namespace = properties.get('namespace', None)
        if install_namespace == None:
            namespace = kube_location.default_object_namespace
        return HelmReleaseConfiguration(chart_path, release_name, install_namespace, values_path)

    def __write_helm_template_to_disk(self, template):
        charts_def = yaml.safe_load(template)
        chart_string = charts_def.get('chart')
        tmp_dir = tempfile.mkdtemp()
        chart_path = os.path.join(tmp_dir, 'chart.tgz')
        with open(chart_path, 'wb') as writer:
            writer.write(base64.b64decode(chart_string))
        values = charts_def.get('values', '')
        values_path = os.path.join(tmp_dir, 'values.yaml')
        with open(values_path, 'w') as writer:
            writer.write(values)
        return chart_path, values_path

    def __render_helm_values_template(self, values_path, system_properties, properties, kube_location):
        render_context = self.template_context_builder.build(system_properties, properties, kube_location.to_dict())
        with open(values_path, 'r') as reader:
            template_output = self.templating.render(reader.read(), render_context)
        with open(values_path, 'w') as writer:
            writer.write(template_output)

    def __generate_helm_release_name(self, system_properties):
        resource_id = system_properties.get('resourceId', None)
        if resource_id == None:
            raise InvalidInfrastructureRequestError('system properties missing \'resourceId\' value')
        resource_name = system_properties.get('resourceName', None)
        if resource_name == None:
            raise InvalidInfrastructureRequestError('system properties missing \'resourceName\' value')
        return name_manager.safe_label_name_for_resource(resource_id, resource_name)
