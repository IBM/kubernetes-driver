import jinja2 as jinja

jinja_env = jinja.Environment(loader=jinja.BaseLoader)

class Template:

    def __init__(self, content_str):
        self.content_str = content_str

    def render(self, input_properties):
        rendered_template_content = jinja_env.from_string(self.content_str).render(input_properties)
        return rendered_template_content
