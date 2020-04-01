from unittest.mock import MagicMock

def create():
    mock_queue = MagicMock()
    worker = ControlledJobQueueWorker()
    worker.bind_to(mock_queue)
    return mock_queue

class ControlledJobQueueWorker():

    def __init__(self, *args, **kwargs):
        self.queued_jobs = []
        self.job_handlers = {}
        
    def bind_to(self, mock):
        mock.register_job_handler.side_effect = self.register_handler
        mock.queue_job.side_effect = self.queue_job
        mock.process_next_job.side_effect = self.process_next_job

    def register_handler(self, job_type, func):
        self.job_handlers[job_type] = func

    def queue_job(self, job):
        self.queued_jobs.append(job)
    
    def process_next_job(self):
        if len(self.queued_jobs) > 0:
            job = self.queued_jobs.pop(0)
            finished = self.job_handlers[job['job_type']](job)
            if not finished:
                self.queue_job(job)
        else:
            raise IndexError('No jobs in queue')