from .name_manager import NameManager

class RenderPropsBuilder:

    @staticmethod
    def build(system_properties, properties):
        return RenderPropsBuilder().build_render_props(system_properties, properties)

    def __init__(self):
        self.name_manager = NameManager()

    def build_render_props(self, system_properties, properties):
        render_props = {k:v for k,v in properties.items()}
        sys_props = {k:v for k,v in system_properties.items()}
        render_props['systemProperties'] = sys_props
        self.__add_additional_render_properties(render_props)
        return render_props

    def __add_additional_render_properties(self, render_props):
        name_manager = NameManager()
        system_properties = render_props['systemProperties']
        self.__add_resource_id_generated_properties(system_properties)
        self.__add_resource_name_generated_properties(system_properties)
        self.__add_resource_combined_generated_properties(system_properties)

    def __add_resource_combined_generated_properties(self, system_properties):
        resource_label = self.name_manager.safe_label_name_for_resource(system_properties.get('resourceId'), system_properties.get('resourceName'))
        system_properties['resourceLabel'] = resource_label
        resource_subdomain = self.name_manager.safe_subdomain_name_for_resource(system_properties.get('resourceId'), system_properties.get('resourceName'))
        system_properties['resourceSd'] = resource_subdomain
        system_properties['resourceSubdomain'] = resource_subdomain

    def __add_resource_id_generated_properties(self, system_properties):
        resoure_id_label = self.name_manager.safe_label_name_from_resource_id(system_properties.get('resourceId'))
        system_properties['resourceIdLabel'] = resoure_id_label
        resource_id_subdomain = self.name_manager.safe_subdomain_name_from_resource_id(system_properties.get('resourceId'))
        system_properties['resourceIdSd'] = resource_id_subdomain
        system_properties['resourceIdSubdomain'] = resource_id_subdomain

    def __add_resource_name_generated_properties(self, system_properties):
        resource_name_label = self.name_manager.safe_label_name_from_resource_name(system_properties.get('resourceName'))
        system_properties['resourceNameLabel'] = resource_name_label
        resource_name_subdomain = self.name_manager.safe_subdomain_name_from_resource_name(system_properties.get('resourceName'))
        system_properties['resourceNameSd'] = resource_name_subdomain
        system_properties['resourceNameSubdomain'] = resource_name_subdomain
