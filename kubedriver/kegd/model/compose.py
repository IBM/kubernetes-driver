class ComposeScript:

    def __init__(self, name, deploy=None, ready_check=None, cleanup_on=None, unique_by=None):
        self.name = name
        self.deploy = deploy if deploy is not None else []
        self.cleanup_on = cleanup_on
        self.unique_by = unique_by
        self.ready_check = ready_check
