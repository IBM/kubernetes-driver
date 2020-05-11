from kubedriver.kegd.model.deploy_task import DeployTask
from kubedriver.kegd.model.removal_task import RemovalTask

class OperationExecution:

    def __init__(self, operation_name, scripts=None, run_cleanup=False):
        self.operation_name = operation_name
        self.scripts = scripts if scripts is not None else []
        self.run_cleanup = run_cleanup

    @staticmethod
    def on_read(operationName=None, scripts=None, runCleanup=None):
        parsed_scripts = []
        if scripts != None:
            for script in scripts:
                parsed_scripts.append(OperationScript.on_read(**script))
        return OperationExecution(operation_name=operationName, scripts=parsed_scripts, run_cleanup=runCleanup)

    def on_write(self):
        write_scripts = []
        for script in self.scripts:
            write_scripts.append(script.on_write())
        return {
            'operationName': self.operation_name,
            'scripts': write_scripts,
            'runCleanup': self.run_cleanup
        }

class OperationScript:

    def __init__(self, name, removal_tasks=None, deploy_tasks=None):
        self.name = name
        self.removal_tasks = removal_tasks if removal_tasks is not None else []
        self.deploy_tasks = deploy_tasks if deploy_tasks is not None else []

    @staticmethod
    def on_read(name=None, removalTasks=None, deployTasks=None):
        parsed_removal_tasks = []
        if removalTasks != None:
            for task in removalTasks:
                parsed_removal_tasks.append(RemovalTask.on_read(**task))
        parsed_deploy_tasks = []
        if deployTasks != None:
            for task in deployTasks:
                parsed_deploy_tasks.append(DeployTask.on_read(**task))
        return OperationScript(name=name, removal_tasks=parsed_removal_tasks, deploy_tasks=parsed_deploy_tasks)

    def on_write(self):
        write_removal_tasks = []
        for task in self.removal_tasks:
            write_removal_tasks.append(task.on_write())
        write_deploy_tasks = []
        for task in self.deploy_tasks:
            write_deploy_tasks.append(task.on_write())
        return {
            'name': self.name,
            'removalTasks': write_removal_tasks,
            'deployTasks': write_deploy_tasks
        }