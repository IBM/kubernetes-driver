from kubedriver.kegd.model.deploy_task import DeployTask
from kubedriver.kegd.model.removal_task import RemovalTask
from .ready_check_task import ReadyCheckTask

class StrategyExecution:

    def __init__(self, operation_name, task_groups=None, ready_check_task=None, run_cleanup=False):
        self.operation_name = operation_name
        self.task_groups = task_groups if task_groups is not None else []
        self.ready_check_task = ready_check_task
        self.run_cleanup = run_cleanup

    @staticmethod
    def on_read(operationName=None, task_groups=None, readyCheckTask=None, runCleanup=None):
        parsed_task_groups = []
        if task_groups != None:
            for script in task_groups:
                parsed_task_groups.append(TaskGroup.on_read(**script))
        parsed_ready_check_task = None
        if readyCheckTask != None:
            parsed_ready_check_task = ReadyCheckTask.on_read(**readyCheckTask)
        return StrategyExecution(operation_name=operationName, task_groups=parsed_task_groups, ready_check_task=parsed_ready_check_task, run_cleanup=runCleanup)

    def on_write(self):
        write_task_groups = []
        for script in self.task_groups:
            write_task_groups.append(script.on_write())
        write_ready_check_task = None
        if self.ready_check_task != None:
            write_ready_check_task = self.ready_check_task.on_write()
        return {
            'operationName': self.operation_name,
            'task_groups': write_task_groups,
            'readyCheckTask': write_ready_check_task,
            'runCleanup': self.run_cleanup
        }

class TaskGroup:

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
        return TaskGroup(name=name, removal_tasks=parsed_removal_tasks, deploy_tasks=parsed_deploy_tasks)

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