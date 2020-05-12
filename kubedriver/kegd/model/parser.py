import yaml
from ignition.service.framework import Service, Capability
from kubedriver.kegd.model.exceptions import InvalidDeploymentStrategyError
from kubedriver.kegd.model.deployment_strategy import DeploymentStrategy, DEFAULT_CLEANUP
from kubedriver.kegd.model.deploy_task import DeployTask
from kubedriver.kegd.model.compose import ComposeScript
from kubedriver.kegd.model.ready_check import ReadyCheck
from kubedriver.kegd.model.output_extraction import OutputExtraction

class DeploymentStrategyParser(Service, Capability):

    def __init__(self, strategy_class=DeploymentStrategy):
        self._strategy_class = strategy_class

    def read_yaml(self, yaml_content):
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise InvalidDeploymentStrategyError(str(e))
        return self.read_dict(data)

    def read_dict(self, data):
        compose = self.__read_compose(data)
        cleanup_on = data.get('cleanupOn', DEFAULT_CLEANUP)
        return self._strategy_class(compose=compose, cleanup_on=cleanup_on)

    def __read_compose(self, data):
        compose = []
        compose_defs = data.get('compose')
        if compose_defs != None:
            if not isinstance(compose_defs, list):
                raise InvalidDeploymentStrategyError(f'compose must be a list but was {type(compose_defs)}')
            seen_names = []
            for compose_def in compose_defs:
                compose_name = compose_def.get('name')
                if compose_name is None:
                    raise InvalidDeploymentStrategyError(f'compose entry missing name {compose_def}')
                if compose_name in seen_names:
                    raise InvalidDeploymentStrategyError(f'compose entry with duplicate name {compose_name}')
                else:
                    seen_names.append(compose_name)
                compose.append(self.__read_compose_def(compose_name, compose_def))
        return compose

    def __read_compose_def(self, compose_name, compose_def):
        deploy_tasks = []
        deploy_task_defs = compose_def.get('deploy')
        if deploy_task_defs != None:
            if not isinstance(deploy_task_defs, list):
                raise InvalidDeploymentStrategyError(f'compose deploy must be a list but was {type(deploy_task_defs)}')
            for deploy_task_def in deploy_task_defs:
                deploy_tasks.append(self.__read_deploy_task(deploy_task_def))
        cleanup_on = compose_def.get('cleanupOn')
        unique_by = compose_def.get('uniqueBy')
        ready_check_def = compose_def.get('checkReady')
        if ready_check_def != None:
            ready_check = self.__read_ready_check_task(ready_check_def)
        else:
            ready_check = None
        extract_output_def = compose_def.get('getOutputs')
        if extract_output_def != None:
            output_extraction = self.__read_output_extraction(extract_output_def)
        else:
            output_extraction = None
        return ComposeScript(compose_name, deploy=deploy_tasks, ready_check=ready_check, output_extraction=output_extraction, cleanup_on=cleanup_on, unique_by=unique_by)
    
    def __read_ready_check_task(self, ready_check_def):
        if isinstance(ready_check_def, str):
            return ReadyCheck(script=ready_check_def)
        elif isinstance(ready_check_def, dict):
            return ReadyCheck.on_read(**ready_check_def)
        else:
            raise InvalidDeploymentStrategyError(f'compose checkReady must be a dict/map or string but found a {type(ready_check_def)}')
    
    def __read_output_extraction(self, extract_output_def):
        if isinstance(extract_output_def, str):
            return OutputExtraction(script=extract_output_def)
        elif isinstance(extract_output_def, dict):
            return OutputExtraction.on_read(**extract_output_def)
        else:
            raise InvalidDeploymentStrategyError(f'compose getOutputs task must be a dict/map or string but found a {type(extract_output_def)}')

    def __read_deploy_task(self, deploy_task_def):
        if not isinstance(deploy_task_def, dict):
            raise InvalidDeploymentStrategyError(f'compose deploy task must be a dict/map but found a {type(deploy_task_def)}')
        return DeployTask.on_read(**deploy_task_def) 

