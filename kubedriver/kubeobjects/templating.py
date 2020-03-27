import logging
import jinja2 as jinja
from ignition.service.framework import Service, Capability
from kubedriver.kubeobjects import ObjectConfigurationTemplate

logger = logging.getLogger(__name__)

class Templating(Service, Capability):

    def render_template(self, template_content, input_properties):
        template = ObjectConfigurationTemplate(template_content)
        doc = template.render(input_properties)
        ##TODO logs sensitive data?
        logger.debug('Template:\n{0}\n---\nResult:\n{1}'.format(template_content, doc.content))
        return doc

    def render_template_as_str(self, template_content, input_properties):
        jinja_env = jinja.Environment(loader=jinja.BaseLoader)
        rendered_template_content = jinja_env.from_string(template_content).render(input_properties)
        return rendered_template_content