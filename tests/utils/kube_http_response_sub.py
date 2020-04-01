##Useful to use in place of a real HttpResponse expected by kubernetes.client.rest.ApiException 
## E.g. ApiException(http_resp=KubeHttpResponse(status=status, reason=reason, data=body))

class KubeHttpResponse:

    def __init__(self, status=None, reason=None, data=None, headers=None):
        self.status = status
        self.reason = reason
        self.data = data
        self.headers = headers

    def getheaders(self):
        return self.headers