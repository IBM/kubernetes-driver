

class TemplateTypes:

    HELM = 'Helm'
    KUBERNETES = 'Kubernetes'
    OBJECT_CONFIG = 'ObjectConfiguration'

    @staticmethod
    def is_object_configuration(template_type):
        lowercase_template_type = template_type.lower()
        return lowercase_template_type == self.OBJECT_CONFIG.lower() or lowercase_template_type == self.KUBERNETES.lower()

    @staticmethod
    def is_helm(template_type):
        lowercase_template_type = template_type.lower()
        return lowercase_template_type == self.HELM.lower()

    @staticmethod
    def describe_possible_values():
        description = f'[{self.OBJECT_CONFIG} (alternative {self.KUBERNETES})'
        description += f', {self.HELM}] (ignoring case)'
        return description