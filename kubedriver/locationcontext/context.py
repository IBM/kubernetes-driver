


class LocationContext:

    def __init__(self, kube_location, api_ctl, kegd_persister, keg_persister):
        self.kube_location = kube_location
        self.api_ctl = api_ctl
        self.kegd_persister = kegd_persister
        self.keg_persister = keg_persister
