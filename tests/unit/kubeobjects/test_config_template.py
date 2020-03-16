import unittest
import yaml
from pathlib import Path
from kubedriver.kubeobjects.config_template import ObjectConfigurationTemplate

def template_path(name):
    return Path(__file__).parent.joinpath('example_templates').joinpath('{0}.template.yaml'.format(name))

def template_content(name):
    with open(template_path(name), 'r') as f:
        content = f.read()
    return content

def expected_result_path(name):
    return Path(__file__).parent.joinpath('example_templates').joinpath('{0}.result.yaml'.format(name))

def expected_result_content(name):
    with open(expected_result_path(name), 'r') as f:
        content = f.read()
    return content

def properties_path(name):
    return Path(__file__).parent.joinpath('example_templates').joinpath('{0}.props.yaml'.format(name))

def properties_content(name):
    with open(properties_path(name), 'r') as f:
        content = f.read()
    return yaml.safe_load(content)

def get_test_template_content(name):
    template = template_content(name)
    props = properties_content(name)
    expected_result = expected_result_content(name)
    return {
        'template': template,
        'props': props,
        'expected_result': expected_result

    }

class TestObjectConfigurationTemplate(unittest.TestCase):

    def __run_happy_path_test_on_group(self, template_group_name):
        test_template_content = get_test_template_content(template_group_name)
        self.__run_happy_path_test(test_template_content)

    def __run_happy_path_test(self, test_template_content):
        res_template = ObjectConfigurationTemplate(test_template_content['template'])
        result = res_template.render(test_template_content['props'])
        self.assertEqual(result.content, test_template_content['expected_result'])

    def test_render(self):
        self.__run_happy_path_test_on_group('simple')

    def test_render_conditional(self):
        self.__run_happy_path_test_on_group('conditional')

    def test_render_multidoc(self):
        self.__run_happy_path_test_on_group('multidoc')