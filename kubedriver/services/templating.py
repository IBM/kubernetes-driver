import logging
from ignition.service.framework import Service, Capability
from kubedriver.kubeobjects import ObjectConfigurationTemplate

logger = logging.getLogger(__name__)

class TemplatingCapability(Capability):

    def render_template(self, template_content, input_properties):
        pass

class Templating(Service, TemplatingCapability):

    def render_template(self, template_content, input_properties):
        template = ObjectConfigurationTemplate(template_content)
        doc = template.render(input_properties)
        ##TODO logs sensitive data?
        logger.debug('Template:\n{0}\n---\nResult:\n{1}'.format(template_content, doc.content))
        return doc