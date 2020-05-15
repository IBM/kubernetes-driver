from ignition.service.templating import ResourceTemplateContextService
from .name_manager import NameManager

class ExtendedResourceTemplateContext(ResourceTemplateContextService):
    
    def __init__(self, name_manager):
        self.name_manager = name_manager

    def _configure_additional_props(self, builder, system_properties, resource_properties, request_properties, deployment_location):
        self.__add_resource_id_generated_properties(builder, system_properties)
        self.__add_resource_name_generated_properties(builder, system_properties)
        self.__add_resource_combined_generated_properties(builder, system_properties)

    def __add_resource_combined_generated_properties(self, builder, system_properties):
        resource_label = self.name_manager.safe_label_name_for_resource(system_properties.get('resourceId'), system_properties.get('resourceName'))
        builder.add_system_property('resourceLabel', resource_label)
        builder.add_system_property('resource_label', resource_label)
        resource_subdomain = self.name_manager.safe_subdomain_name_for_resource(system_properties.get('resourceId'), system_properties.get('resourceName'))
        builder.add_system_property('resourceSd', resource_subdomain)
        builder.add_system_property('resource_sd', resource_subdomain)
        builder.add_system_property('resourceSubdomain', resource_subdomain)
        builder.add_system_property('resource_subdomain', resource_subdomain)

    def __add_resource_id_generated_properties(self, builder, system_properties):
        resoure_id_label = self.name_manager.safe_label_name_from_resource_id(system_properties.get('resourceId'))
        builder.add_system_property('resourceIdLabel', resoure_id_label)
        builder.add_system_property('resource_id_label', resoure_id_label)
        resource_id_subdomain = self.name_manager.safe_subdomain_name_from_resource_id(system_properties.get('resourceId'))
        builder.add_system_property('resourceIdSd', resource_id_subdomain)
        builder.add_system_property('resource_id_sd', resource_id_subdomain)
        builder.add_system_property('resourceIdSubdomain', resource_id_subdomain)
        builder.add_system_property('resource_id_subdomain', resource_id_subdomain)

    def __add_resource_name_generated_properties(self, builder, system_properties):
        resource_name_label = self.name_manager.safe_label_name_from_resource_name(system_properties.get('resourceName'))
        builder.add_system_property('resourceNameLabel', resource_name_label)
        builder.add_system_property('resource_name_label', resource_name_label)
        resource_name_subdomain = self.name_manager.safe_subdomain_name_from_resource_name(system_properties.get('resourceName'))
        builder.add_system_property('resourceNameSd', resource_name_subdomain)
        builder.add_system_property('resource_name_sd', resource_name_subdomain)
        builder.add_system_property('resourceNameSubdomain', resource_name_subdomain)
        builder.add_system_property('resource_name_subdomain', resource_name_subdomain)
