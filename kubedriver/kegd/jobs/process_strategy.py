from kubedriver.location import KubeDeploymentLocation
from kubedriver.kegd.model.operation_execution import OperationExecution

class ProcessStrategyJob:

    job_type = 'ProcessStrategy'

    def __init__(self, request_id, kube_location, keg_name, operation_execution):
        self.request_id = request_id
        self.kube_location = kube_location
        self.keg_name = keg_name
        self.operation_execution = operation_execution

    @staticmethod
    def on_read(request_id=None, kube_location=None, keg_name=None, operation_execution=None):
        if kube_location != None:
            kube_location = KubeDeploymentLocation.from_dict(kube_location)
        if operation_execution != None:
            operation_execution = OperationExecution.on_read(**operation_execution)
        return ProcessStrategyJob(request_id=request_id, kube_location=kube_location, keg_name=keg_name, operation_execution=operation_execution)

    def on_write(self):
        write_operation_execution = None
        if self.operation_execution != None:
            write_operation_execution = self.operation_execution.on_write()
        return {
            'kube_location': self.kube_location.to_dict(), 
            'keg_name': self.keg_name,
            'request_id': self.request_id,
            'operation_execution': write_operation_execution
        }