
class HelmTls:

    def __init__(self, enabled=False, ca_cert=None, cert=None, key=None):
        self.enabled = enabled
        self.ca_cert = ca_cert
        self.cert = cert
        self.key = key