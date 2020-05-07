from kubedriver.kegd.model.deploy_task import DeployTask
from kubedriver.kegd.model.withdraw_task import WithdrawTask
from kubedriver.location import KubeDeploymentLocation

class ProcessStrategyJob:

    job_type = 'ProcessStrategy'

    def __init__(self, request_id, kube_location, keg_name, operation_name, withdraw_tasks, deploy_tasks):
        self.request_id = request_id
        self.kube_location = kube_location
        self.keg_name = keg_name
        self.operation_name = operation_name
        self.withdraw_tasks = withdraw_tasks if withdraw_tasks is not None else []
        self.deploy_tasks = deploy_tasks if deploy_tasks is not None else []

    @staticmethod
    def on_read(request_id=None, kube_location=None, keg_name=None,operation_name=None, withdraw_tasks=None, deploy_tasks=None):
        if kube_location != None:
            kube_location = KubeDeploymentLocation.from_dict(kube_location)
        parsed_withdraw_tasks = []
        if withdraw_tasks != None:
            for task in withdraw_tasks:
                parsed_withdraw_tasks.append(WithdrawTask.on_read(**task))
        parsed_deploy_tasks = []
        if deploy_tasks != None:
            for task in deploy_tasks:
                parsed_deploy_tasks.append(DeployTask.on_read(**task))
        return ProcessStrategyJob(request_id=request_id, kube_location=kube_location, keg_name=keg_name, operation_name=operation_name, withdraw_tasks=parsed_withdraw_tasks, deploy_tasks=parsed_deploy_tasks)

    def on_write(self):
        write_withdraw_tasks = []
        for task in self.withdraw_tasks:
            write_withdraw_tasks.append(task.on_write())
        write_deploy_tasks = []
        for task in self.deploy_tasks:
            write_deploy_tasks.append(task.on_write())
        return {
            'kube_location': self.kube_location.to_dict(), 
            'keg_name': self.keg_name,
            'request_id': self.request_id,
            'operation_name': self.operation_name,
            'withdraw_tasks': write_withdraw_tasks,
            'deploy_tasks': write_deploy_tasks
        }