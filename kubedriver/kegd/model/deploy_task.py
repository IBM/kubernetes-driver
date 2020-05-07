from .deploy_objects_action import DeployObjectsAction
from .deploy_object_action import DeployObjectAction
from .deploy_helm_action import DeployHelmAction
from .exceptions import InvalidDeploymentStrategyError

ACCEPTED_ACTIONS = {
    DeployHelmAction.action_name: DeployHelmAction, 
    DeployObjectAction.action_name: DeployObjectAction,
    DeployObjectsAction.action_name: DeployObjectsAction
}

class DeployTask:

    def __init__(self, settings, action):
        self.action = action
        self.settings = settings

    def on_write(self):
        data = {
            self.action.action_name: self.action.write()
        }
        data.update(self.settings.write())
        return data

    @staticmethod
    def on_read(**kwargs):
        settings, remainder = DeployTaskSettings.on_read(**kwargs)
        if len(remainder) != 1:
            raise InvalidDeploymentStrategyError(f'compose deploy task must specify one type from {ACCEPTED_ACTIONS.keys()} but found multiple {remainder.keys()}')
        action_name = remainder.keys()[0]
        if action_name not in ACCEPTED_ACTIONS:
            raise InvalidDeploymentStrategyError(f'compose deploy task must specify one type from {ACCEPTED_ACTIONS.keys()} not {action_name}')
        action_args = remainder.get(action_name, {})
        if not isinstance(action_args, dict):
            raise InvalidDeploymentStrategyError(f'compose deploy task arguments must be a dict/map but was {type(action_args)}')
        action = ACCEPTED_ACTIONS.get(action_name).on_read(**action_args)
        return DeployTask(settings=settings, action=action)

class DeployTaskSettings:

    def __init__(self):
        pass

    @staticmethod
    def on_read(**kwargs):
        return (DeployTaskSettings(), kwargs)

    @staticmethod
    def on_write(settings):
        return {}
