from .remove_object_action import RemoveObjectAction
from .remove_helm_action import RemoveHelmAction
from .exceptions import InvalidDeploymentStrategyError

ACCEPTED_ACTIONS = {
    RemoveObjectAction.action_name: RemoveObjectAction,
    RemoveHelmAction.action_name: RemoveHelmAction
}

class RemovalTask:

    def __init__(self, settings, action):
        self.action = action
        self.settings = settings

    def on_write(self):
        data = {
            self.action.action_name: self.action.on_write()
        }
        data.update(self.settings.on_write())
        return data

    @staticmethod
    def on_read(**kwargs):
        settings, remainder = RemovalTaskSettings.on_read(**kwargs)
        if len(remainder) != 1:
            raise InvalidDeploymentStrategyError(f'compose remove task must specify one type from {ACCEPTED_ACTIONS.keys()} but found multiple {remainder.keys()}')
        action_name = list(remainder.keys())[0]
        if action_name not in ACCEPTED_ACTIONS:
            raise InvalidDeploymentStrategyError(f'compose remove task must specify one type from {ACCEPTED_ACTIONS.keys()} not {action_name}')
        action_args = remainder.get(action_name, {})
        if not isinstance(action_args, dict):
            raise InvalidDeploymentStrategyError(f'compose remove task arguments must be a dict/map but was {type(action_args)}')
        action = ACCEPTED_ACTIONS.get(action_name).on_read(**action_args)
        return RemovalTask(settings=settings, action=action)

class RemovalTaskSettings:

    def __init__(self):
        pass

    @staticmethod
    def on_read(**kwargs):
        return (RemovalTaskSettings(), kwargs)

    def on_write(self):
        return {}
