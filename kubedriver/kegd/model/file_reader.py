import os
from ignition.templating import Syntax
from ignition.service.framework import Service, Capability
from kubedriver.kegd.model.exceptions import InvalidDeploymentStrategyError

class DeploymentStrategyFileReader(Service, Capability):

    def __init__(self, deployment_strategy_properties, templating, parser):
        self.deployment_strategy_properties = deployment_strategy_properties
        self.templating_enabled = False
        self.templating = templating
        self.parser = parser

    def read(self, file_path, render_context):
        file_contents = self.__read_file_contents(file_path)
        templated_content = self.__render(file_contents, render_context)
        deployment_strategy = self.__parse(templated_content)
        return deployment_strategy

    def __read_file_contents(self, file_path):
        if not os.path.exists(file_path):
            raise InvalidDeploymentStrategyError(f'Could not find file: {file_path}')
        with open(file_path, 'r') as f:
            file_content = f.read()
        return file_content

    def __render(self, file_contents, render_context):
        if not self.templating_enabled:
            return file_contents
        settings = None
        if self.templating.syntax() == Syntax.JINJA2:
            settings = self.templating.build_settings()
            settings.update(self.deployment_strategy_properties.templating.syntax)
        return self.templating.render(file_contents, render_context, settings=settings)

    def __parse(self, file_contents):
        return self.parser.read_yaml(file_contents)