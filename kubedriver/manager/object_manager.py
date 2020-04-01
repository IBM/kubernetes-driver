import uuid
import logging
from kubernetes.client.rest import ApiException
from ignition.service.framework import Service, Capability
from .records import ObjectRecord, GroupRecord, RequestRecord, HelmRecord, ObjectStates, RequestStates, RequestOperations
from .exceptions import RequestInvalidStateError, RecordNotFoundError, RecordNotFoundError
from kubedriver.kubeclient import ErrorReader, DEFAULT_NAMESPACE
from kubedriver.kubeobjects import ObjectConfiguration
from kubedriver.location import KubeDeploymentLocation

logger = logging.getLogger(__name__)

CREATE_JOB = 'kom.CreateObjectGroup'
DELETE_JOB = 'kom.DeleteObjectGroup'

class KubeObjectManager(Service, Capability):

    def __init__(self, context_loader, job_queue, error_reader=None):
        self.context_loader = context_loader
        self.job_queue = job_queue
        self.error_reader = error_reader if error_reader is not None else ErrorReader()
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
        group_record = context.record_persistence.get(group_uid)
        request_id, job_data = self.__initiate_delete_job(context.location, group_record)
        context.record_persistence.update(group_record)
        self.job_queue.queue_job(job_data)
        return request_id

    def get_group_record(self, kube_location, group_uid):
        context = self.context_loader.load(kube_location)
        return context.record_persistence.get(group_uid)

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
        helm_release_records = []
        for helm_release in object_group.helm_releases:
            helm_release_records.append(HelmRecord(helm_release.chart, helm_release.name, helm_release.namespace, helm_release.values))
        group_record = GroupRecord(object_group.identifier, object_records, helm_releases=helm_release_records, requests=[])
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
        return self.__process_request(context, group_uid, request_uid)

    def __process_request(self, context, group_uid, request_uid):
        # Errors retrieving the group, request or checking request state result in the job not being requeued
        group_record = context.record_persistence.get(group_uid)
        request_record = self.__find_request_record(group_record, request_uid)
        if request_record.state != RequestStates.PENDING:
            raise RequestInvalidStateError(f'Request with uid \'{request_uid}\' cannot be processed as it is in the \'{request_record.state}\' state')
        request_record.state = RequestStates.IN_PROGRESS
        context.record_persistence.update(group_record)
        # This point forward we must make best efforts to update the request if there is an error
        request_errors = None
        try:
            if request_record.operation == RequestOperations.CREATE:
                request_errors = self.__process_create(context, group_record, request_record)
            else:
                request_errors = self.__process_delete(context, group_record, request_record)
        except Exception as e:
            logger.exception(f'An error occurred whilst processing request {request_uid} on Group {group_uid}, attempting to update records with failure')
            if request_errors is None:
                request_errors = []
            request_errors.append(f'Internal error: {str(e)}')
        # If we can't update the record then we can't do much else TODO: retry the request and/or update
        self.__update_request_with_results(request_record, request_errors)
        context.record_persistence.update(group_record)
        # Finished the job
        return True

    def __process_create(self, context, group_record, request_record):
        request_errors = []
        object_request_errors = self.__create_objects(context, group_record, request_record)
        request_errors.extend(object_request_errors)
        helm_request_errors = self.__create_helm_releases(context, group_record, request_record)
        request_errors.extend(helm_request_errors)
        return request_errors

    def __create_objects(self, context, group_record, request_record):
        request_errors = []
        for object_record in group_record.objects:
            try:
                context.api_ctl.create_object(ObjectConfiguration(object_record.config), default_namespace=context.location.default_object_namespace)
                object_record.state = ObjectStates.CREATED
                object_record.error = None
            except Exception as e:
                logger.exception(f'Create attempt of Object ({object_record}) in Group \'{group_record.uid}\' failed')
                error_msg = str(e)
                request_errors.append(error_msg)
                object_record.state = ObjectStates.CREATE_FAILED
                object_record.error = error_msg
        return request_errors

    def __create_helm_releases(self, context, group_record, request_record):
        request_errors = []
        for helm_release_record in group_record.helm_releases:
            try:
                context.helm_client.install(helm_release_record.chart, helm_release_record.name, helm_release_record.namespace, helm_release_record.values)
                helm_release_record.state = ObjectStates.CREATED
                helm_release_record.error = None
            except Exception as e:
                logger.exception(f'Create attempt of Helm Release ({helm_release_record}) in Group \'{group_record.uid}\' failed')
                error_msg = str(e)
                request_errors.append(error_msg)
                helm_release_record.state = ObjectStates.CREATE_FAILED
                helm_release_record.error = error_msg
        return request_errors

    def __process_delete(self, context, group_record, request_record):
        request_errors = []
        object_request_errors = self.__delete_objects(context, group_record, request_record)
        request_errors.extend(object_request_errors)
        helm_request_errors = self.__delete_helm_releases(context, group_record, request_record)
        request_errors.extend(helm_request_errors)
        return request_errors

    def __delete_objects(self, context, group_record, request_record):
        request_errors = []
        for object_record in group_record.objects:
            try:
                if object_record.state != ObjectStates.CREATE_FAILED and object_record.state != ObjectStates.DELETED:
                    object_config = ObjectConfiguration(object_record.config)
                    namespace = object_config.namespace
                    if namespace is None:
                        namespace = context.location.default_object_namespace
                    try:
                        context.api_ctl.delete_object(object_config.api_version, object_config.kind, object_config.name, namespace=namespace)
                    except ApiException as e:
                        logger.exception(f'Delete attempt of Object ({object_record}) in Group \'{group_record.uid}\' failed')
                        # If not found, we assume it was deleted
                        if self.error_reader.is_not_found_err(e):
                            logger.warn(f'Attempt to delete Object (api_version={object_config.api_version}, kind={object_config.kind}, name={object_config.name}) in Group \'{group_record.uid}\' returned \'Not Found\', assuming this has already been deleted')
                        else:
                            # Raise original error and trackeback
                            raise
                    object_record.state = ObjectStates.DELETED
                    object_record.error = None
            except Exception as e:
                error_msg = str(e)
                request_errors.append(error_msg)
                object_record.state = ObjectStates.DELETE_FAILED
                object_record.error = error_msg
        return request_errors

    def __delete_helm_releases(self, context, group_record, request_record):
        request_errors = []
        for helm_release_record in group_record.helm_releases:
            try:
                if helm_release_record.state != ObjectStates.CREATE_FAILED and helm_release_record.state != ObjectStates.DELETED:
                    context.helm_client.purge(helm_release_record.name)
                    #TODO handle "Not found"
                    helm_release_record.state = ObjectStates.DELETED
                    helm_release_record.error = None
            except Exception as e:
                logger.exception(f'Delete attempt of Helm Release ({helm_release_record}) in Group \'{group_record.uid}\' failed')
                error_msg = str(e)
                request_errors.append(error_msg)
                helm_release_record.state = ObjectStates.DELETE_FAILED
                helm_release_record.error = error_msg
        return request_errors

    def __update_request_with_results(self, request_record, request_errors):
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
        raise RecordNotFoundError('Request with uid \'{0}\' not found on Group \'{1}\''.format(request_uid, request_uid))
