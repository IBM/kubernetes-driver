from kubedriver.location import KubeDeploymentLocation
from kubedriver.kegd.model.strategy_execution import StrategyExecution
from kubedriver.kegd.model.retry_status import RetryStatus

class ProcessStrategyJob:

    job_type = 'ProcessStrategy'

    def __init__(self, request_id, kube_location, keg_name, strategy_execution, resource_context_properties, retry_status=None):
        self.request_id = request_id
        self.kube_location = kube_location
        self.keg_name = keg_name
        self.strategy_execution = strategy_execution
        self.resource_context_properties = resource_context_properties
        self.retry_status = retry_status

    @staticmethod
    def on_read(request_id=None, kube_location=None, keg_name=None, strategy_execution=None, resource_context_properties=None, retry_status=None):
        if kube_location != None:
            kube_location = KubeDeploymentLocation.from_dict(kube_location)
        if strategy_execution != None:
            strategy_execution = StrategyExecution.on_read(**strategy_execution)
        if retry_status != None:
            retry_status = RetryStatus.on_read(**retry_status)
        return ProcessStrategyJob(request_id=request_id, kube_location=kube_location, keg_name=keg_name, 
                                        strategy_execution=strategy_execution, resource_context_properties=resource_context_properties,
                                        retry_status=retry_status)

    def on_write(self):
        write_strategy_execution = None
        if self.strategy_execution != None:
            write_strategy_execution = self.strategy_execution.on_write()
        write_retry_status = None
        if self.retry_status != None:
            write_retry_status = self.retry_status.on_write()
        return {
            'kube_location': self.kube_location.to_dict(), 
            'keg_name': self.keg_name,
            'request_id': self.request_id,
            'strategy_execution': write_strategy_execution,
            'resource_context_properties': self.resource_context_properties,
            'retry_status': write_retry_status
        }