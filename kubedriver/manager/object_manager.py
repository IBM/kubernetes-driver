import uuid
import logging
from ignition.service.framework import Service, Capability
from .records import ObjectRecord, GroupRecord, RequestRecord, ObjectStates, RequestStates, RequestOperations
from .exceptions import RequestInvalidStateError, RequestNotFoundError
from kubedriver.kubeclient.defaults import DEFAULT_NAMESPACE
from kubedriver.kubeobjects import ObjectConfiguration
from kubedriver.location import KubeDeploymentLocation

logger = logging.getLogger(__name__)

CREATE_JOB = 'kom.CreateObjectGroup'
DELETE_JOB = 'kom.DeleteObjectGroup'

class KubeObjectManager(Service, Capability):

    def __init__(self, context_loader, job_queue):
        self.context_loader = context_loader
        self.job_queue = job_queue
        self.job_queue.register_job_handler(CREATE_JOB, self.__handler_for_job)
        self.job_queue.register_job_handler(DELETE_JOB, self.__handler_for_job)

    def create_group(self, kube_location, object_group):
        context = self.context_loader.load(kube_location)
        group_record = self.__initiate_record(context, object_group)
        request_id, job_data = self.__initiate_create_job(context.location, group_record)
        context.record_persistence.create(group_record)
        self.job_queue.queue_job(job_data)
        return request_id

    def delete_group(self, kube_location, group_uid):
        context = self.context_loader.load(kube_location)
        #TODO group not found?
        group_record = context.record_persistence.get(group_uid)
        request_id, job_data = self.__initiate_delete_job(context.location, group_record)
        context.record_persistence.update(group_record)
        self.job_queue.queue_job(job_data)
        return request_id

    def get_request_record(self, kube_location, group_uid, request_uid):
        context = self.context_loader.load(kube_location)
        group_record = context.record_persistence.get(group_uid)
        return self.__find_request_record(group_record, request_uid)

    def purge_group(self, kube_location, group_uid):
        context = self.context_loader.load(kube_location)
        context.record_persistence.delete(group_uid)

    def __initiate_record(self, context, object_group):
        object_records = []
        for object_conf in object_group.objects:
            object_records.append(ObjectRecord(object_conf.config, state=ObjectStates.PENDING))
        group_record = GroupRecord(object_group.identifier, object_records, [])
        return group_record

    def __initiate_create_job(self, kube_location, group_record):
        request_uid = str(uuid.uuid4())
        create_job_data = self.__build_create_job_data(group_record.uid, request_uid, kube_location)
        request_record = RequestRecord(request_uid, RequestOperations.CREATE, state=RequestStates.PENDING)
        group_record.requests.append(request_record)
        return request_uid, create_job_data

    def __initiate_delete_job(self, kube_location, group_record):
        request_uid = str(uuid.uuid4())
        delete_job_data = self.__build_delete_job_data(group_record.uid, request_uid, kube_location)
        request_record = RequestRecord(request_uid, RequestOperations.DELETE, state=RequestStates.PENDING)
        group_record.requests.append(request_record)
        return request_uid, delete_job_data

    def __build_create_job_data(self, group_uid, request_uid, kube_location):
        return {
            'job_type': CREATE_JOB,
            'group_uid': group_uid,
            'request_uid': request_uid,
            'kube_location': kube_location.to_dict()
        }

    def __build_delete_job_data(self, group_uid, request_uid, kube_location):
        return {
            'job_type': DELETE_JOB,
            'group_uid': group_uid,
            'request_uid': request_uid,
            'kube_location': kube_location.to_dict()
        }
    
    def __handler_for_job(self, job):
        kube_location = KubeDeploymentLocation.from_dict(job.get('kube_location'))
        context = self.context_loader.load(kube_location)
        group_uid = job.get('group_uid')
        request_uid = job.get('request_uid')
        self.__process_request(context, group_uid, request_uid)
        return True

    def __process_request(self, context, group_uid, request_uid):
        group_record = context.record_persistence.get(group_uid)
        request_record = self.__find_request_record(group_record, request_uid)
        if request_record.state != RequestStates.PENDING:
            raise RequestInvalidStateError('Request with uid \'{0}\' cannot be processed as it is in the \'{1}\' state'.format(request_uid, request_record.state))
        request_record.state = RequestStates.IN_PROGRESS
        context.record_persistence.update(group_record)
        if request_record.operation == RequestOperations.CREATE:
            request_errors = self.__process_create(context, group_record, request_record)
        else:
            request_errors = self.__process_delete(context, group_record, request_record)
        self.__post_process_update_request(request_record, request_errors)
        context.record_persistence.update(group_record)

    def __process_create(self, context, group_record, request_record):
        request_errors = []
        for object_record in group_record.objects:
            try:
                context.api_ctl.create_object(ObjectConfiguration(object_record.config), default_namespace=context.location.default_object_namespace)
                object_record.state = ObjectStates.CREATED
                object_record.error = None
            except Exception as e:
                error_msg = str(e)
                request_errors.append(error_msg)
                object_record.state = ObjectStates.CREATE_FAILED
                object_record.error = error_msg
        return request_errors

    def __process_delete(self, context, group_record, request_record):
        request_errors = []
        for object_record in group_record.objects:
            try:
                if object_record.state != ObjectStates.CREATE_FAILED and object_record.state != ObjectStates.DELETED:
                    object_config = ObjectConfiguration(object_record.config)
                    namespace = object_config.namespace
                    if namespace is None:
                        namespace = context.location.default_object_namespace
                    context.api_ctl.delete_object(object_config.api_version, object_config.kind, object_config.name, namespace=namespace)
                    object_record.state = ObjectStates.DELETED
                    object_record.error = None
            except Exception as e:
                error_msg = str(e)
                request_errors.append(error_msg)
                object_record.state = ObjectStates.DELETE_FAILED
                object_record.error = error_msg
        return request_errors

    def __post_process_update_request(self, request_record, request_errors):
        if len(request_errors) > 0:
            request_record.state = RequestStates.FAILED
            request_record.error = self.__summarise_request_errors(request_errors)
        else:
            request_record.state = RequestStates.COMPLETE
            request_record.error = None
        
    def __summarise_request_errors(self, request_errors):
        error_msg = 'Request encountered {0} error(s):'.format(len(request_errors))
        for idx, error in enumerate(request_errors):
            error_msg += '\n\t{0} - {1}'.format(idx+1, error)
        return error_msg

    def __find_request_record(self, group_record, request_uid):
        for request_record in group_record.requests:
            if request_record.uid == request_uid:
                return request_record
        raise RequestNotFoundError('Request with uid \'{0}\' not found on Group \'{1}\''.format(request_uid, group_record.uid))
