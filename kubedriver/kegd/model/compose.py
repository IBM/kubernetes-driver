class ComposeScript:

    def __init__(self, name, deploy=None, reverse=None):
        self.name = name
        self.deploy = deploy if deploy is not None else []
        self.reverse = reverse
