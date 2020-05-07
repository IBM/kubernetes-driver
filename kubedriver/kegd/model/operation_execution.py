from kubedriver.kegd.model.deploy_task import DeployTask
from kubedriver.kegd.model.withdraw_task import WithdrawTask

class OperationExecution:

    def __init__(self, operation_name, scripts=None, run_cleanup=False):
        self.operation_name = operation_name
        self.scripts = scripts if scripts is not None else []
        self.run_cleanup = run_cleanup

    @staticmethod
    def on_read(operation_name=None, scripts=None, run_cleanup=None):
        parsed_scripts = []
        if scripts != None:
            for script in scripts:
                parsed_scripts.append(OperationScript.on_read(**script))
        return OperationExecution(operation_name=operation_name, scripts=parsed_scripts, run_cleanup=run_cleanup)

    def on_write(self):
        write_scripts = []
        for script in self.scripts:
            write_scripts.append(script.on_write())
        return {
            'operation_name': self.operation_name,
            'scripts': write_scripts,
            'run_cleanup': self.run_cleanup
        }

class OperationScript:

    def __init__(self, name, withdraw_tasks=None, deploy_tasks=None):
        self.name = name
        self.withdraw_tasks = withdraw_tasks if withdraw_tasks is not None else []
        self.deploy_tasks = deploy_tasks if deploy_tasks is not None else []

    @staticmethod
    def on_read(name=None, withdraw_tasks=None, deploy_tasks=None):
        parsed_withdraw_tasks = []
        if withdraw_tasks != None:
            for task in withdraw_tasks:
                parsed_withdraw_tasks.append(WithdrawTask.on_read(**task))
        parsed_deploy_tasks = []
        if deploy_tasks != None:
            for task in deploy_tasks:
                parsed_deploy_tasks.append(DeployTask.on_read(**task))
        return OperationScript(name=name, withdraw_tasks=parsed_withdraw_tasks, deploy_tasks=parsed_deploy_tasks)

    def on_write(self):
        write_withdraw_tasks = []
        for task in self.withdraw_tasks:
            write_withdraw_tasks.append(task.on_write())
        write_deploy_tasks = []
        for task in self.deploy_tasks:
            write_deploy_tasks.append(task.on_write())
        return {
            'name': self.name,
            'withdraw_tasks': write_withdraw_tasks,
            'deploy_tasks': write_deploy_tasks
        }