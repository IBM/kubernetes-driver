

class TemplateTypes:

    HELM = 'Helm'
    KUBERNETES = 'Kubernetes'
    OBJECT_CONFIG = 'ObjectConfiguration'

    @staticmethod
    def is_object_configuration(template_type):
        lowercase_template_type = template_type.lower()
        return lowercase_template_type == TemplateTypes.OBJECT_CONFIG.lower() or lowercase_template_type == TemplateTypes.KUBERNETES.lower()

    @staticmethod
    def is_helm(template_type):
        lowercase_template_type = template_type.lower()
        return lowercase_template_type == TemplateTypes.HELM.lower()

    @staticmethod
    def describe_possible_values():
        description = f'[{TemplateTypes.OBJECT_CONFIG} (alternative {TemplateTypes.KUBERNETES})'
        description += f', {TemplateTypes.HELM}] (ignoring case)'
        return description