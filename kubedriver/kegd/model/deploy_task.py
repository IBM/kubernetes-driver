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
            self.action.action_name: self.action.on_write()
        }
        data.update(self.settings.on_write())
        return data

    @staticmethod
    def on_read(**kwargs):
        settings, remainder = DeployTaskSettings.on_read(**kwargs)
        if len(remainder) != 1:
            raise InvalidDeploymentStrategyError(f'compose deploy task must specify one type from {ACCEPTED_ACTIONS.keys()} but found multiple {remainder.keys()}')
        action_name = list(remainder.keys())[0]
        if action_name not in ACCEPTED_ACTIONS:
            raise InvalidDeploymentStrategyError(f'compose deploy task must specify one type from {ACCEPTED_ACTIONS.keys()} not {action_name}')
        action_args = remainder.get(action_name, {})
        if not isinstance(action_args, dict):
            raise InvalidDeploymentStrategyError(f'compose deploy task arguments must be a dict/map but was {type(action_args)}')
        action = ACCEPTED_ACTIONS.get(action_name).on_read(**action_args)
        return DeployTask(settings=settings, action=action)

class DeployTaskSettings:

    IMMEDIATE_CLEANUP_NEVER = 'Never'
    IMMEDIATE_CLEANUP_SUCCESS = 'Success'
    IMMEDIATE_CLEANUP_FAILURE = 'Failure'
    IMMEDIATE_CLEANUP_ALWAYS = 'Always'
    
    def __init__(self, immediate_cleanup_on=None):
        if immediate_cleanup_on == None:
            immediate_cleanup_on = DeployTaskSettings.IMMEDIATE_CLEANUP_NEVER
        self.immediate_cleanup_on = immediate_cleanup_on

    @staticmethod
    def on_read(immediateCleanupOn=None, **kwargs):
        if immediateCleanupOn == None:
            immediateCleanupOn = DeployTaskSettings.IMMEDIATE_CLEANUP_NEVER
        allowed_cleanup_values = [DeployTaskSettings.IMMEDIATE_CLEANUP_NEVER, DeployTaskSettings.IMMEDIATE_CLEANUP_SUCCESS, 
                                            DeployTaskSettings.IMMEDIATE_CLEANUP_FAILURE, DeployTaskSettings.IMMEDIATE_CLEANUP_ALWAYS]
        if immediateCleanupOn not in allowed_cleanup_values:
            raise InvalidDeploymentStrategyError(f'immediateCleanupOn value must be one of: {allowed_cleanup_values}')
        return (DeployTaskSettings(immediate_cleanup_on=immediateCleanupOn), kwargs)

    def on_write(self):
        return {
            'immediateCleanupOn': self.immediate_cleanup_on
        }
