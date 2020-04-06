

class RenderPropsBuilder:

    @staticmethod
    def build(self, system_properties, properties):
        return RenderPropsBuilder().build_render_props(system_properties, properties)

    def build_render_props(self, system_properties, properties):
        render_props = {k:v for k,v in properties.items()}
        sys_props = {k:v for k,v in system_properties.items()}
        render_props['systemProperties'] = sys_props
        self.__add_additional_render_properties(render_props)
        return render_props

    def __add_additional_render_properties(self, render_props):
        system_properties = render_props['systemProperties']
        if 'resourceId' in system_properties:
            system_properties['resourceIdSd'] = namehelper.safe_subdomain_name(system_properties.get('resourceId'))
            system_properties['resourceIdSubdomain'] = namehelper.safe_subdomain_name(system_properties.get('resourceId'))
        if 'resourceName' in system_properties:
            system_properties['resourceNameSd'] = namehelper.safe_subdomain_name(system_properties.get('resourceName'))
            system_properties['resourceNameSubdomain'] = namehelper.safe_subdomain_name(system_properties.get('resourceName'))
