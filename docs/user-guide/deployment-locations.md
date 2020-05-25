# Deployment Locations

A deployment location must be provided to an infrastructure request to indicate the Kubernetes environment to be used. The deployment location will be managed by the Lifecycle Manager and Brent but must have particular properties to be successfully used by this driver.

# Properties

The following properties are supported by the driver:


| Name            | Default | Required                           | Detail                                                                                                                     |
| --------------- | ------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| clientConfig      | -       | Y                                  | A multiline string version of the kubectl config file used to access the target cluster (see more details [below](#obtaining-clientconfig)) |
| crdApiVersion | apiextensions.k8s.io/v1beta1    | N                                  | To deploy custom resource types in Kubernetes the CRD API version is required. Only update this if a later release of Kubernetes upgrades the API version |
| defaultObjectNamespace | default | N | Sets the default namespace used when deploying Kubernetes objects on a create request. This value is only used when the object does not have a specified namespace in the metadata section of it's configuration |
| driverNamespace     | Value of defaultObjectNamepsace/default_object_namespace      | N | Sets the namespace to be used by the driver for any Kubernetes objects it creates for management purposes |
| helm.version     | 2.8.2      | N | Determines the helm client version to use when deploying helm charts (allowed values: 2.8.2, 2.16.7) |
| helm.tls.enabled | False | N | Enable `--tls` option on the helm client. You will need to provide the cert/key pair (see [Helm TLS](#helm-tls)) |
| helm.tls.cacert | - | N | Contents of the CA certificate (if used) |
| helm.tls.cert | - | N | Contents of the helm client certificate |
| helm.tls.key | - | N | Contents of the helm client key |

**Note:** when using Helm your target deployment location must be using a compatible server version for 2.8.2 or 2.16.7 (check with `helm version` on the server).

# Obtaining clientConfig

## Kubeadm 

The easiest way to obtain the client configuration for your Kubernetes cluster is to run the `config view` command from a machine with existing kubectl access:

```
# --raw is required to prevent omission certificate values
kubectl config view --raw
```

This will output a YAML document. If you don't have kubectl access you can obtain this document by accessing `/etc/kubernetes/admin.conf` from your Kubernetes master host:

```
sudo cat /etc/kubernetes/admin.conf
```

Copy the contents from the console (or file) into your deployment location properties as a multiline string value:

```
clientConfig: |
  apiVersion: v1
  clusters:
  - cluster:
      certificate-authority-data: <sensitive data removed from docs>
      server: https://1.2.3.4:6443
    name: kubernetes
  contexts:
  - context:
      cluster: kubernetes
      user: kubernetes-admin
    name: kubernetes-admin@kubernetes
  current-context: kubernetes-admin@kubernetes
  kind: Config
  preferences: {}
  users:
  - name: kubernetes-admin
    user:
      client-certificate-data: <sensitive data removed from docs>
```

Only use this method if you are comfortable with the user in use and the permissions they have been granted through their role bindings.

## Microk8s

For microk8s, you may try `kubectl config view` but you may notice the server address as `127.0.0.1` which is not going to work for remote connections.

Instead, try:

```
microk8s.config
```

If this commands fails with "unrecognised" but you know you have microk8s installed, make the sure your `snap` bin is on your `PATH` environment variable (usually `/snap/bin`).

# Helm TLS

You need to configure the `helm.tls` properties if you would normally add the `--tls` option when executing `helm` commands against your target environment, for example:

```
helm ls --tls
```

If you remove the `--tls` option you'll likely see `Error: transport is closing`. 

If TLS is enabled, you must add the contents of the certificate and keys to the deployment location. These files will usually be in the helm home directory (on the server you use the helm CLI from):

```
ls $(helm home)

cache  ca.pem  cert.pem  key.pem  plugins  repository  starters
```

The files may have different names and you may not have a CA file (`ca.pem`). 

If you normally provide custom paths with the `--tls-ca-cert`, `--tls-cert` and `--tls-key` options then use those files instead.

Once you've identified the certificate and key files used by your helm CLI, obtain their contents by printing to the console (or open in a text editor):

```
cat $(helm home)/cert.pem
```

Copy the contents from the console (or file) into your deployment location properties as a multiline string value:

```
helm.tls.cert: |
  -----BEGIN CERTIFICATE-----
  MIIFWjCCA0ICCQD5Avb/OJ3QcTANBgkqhkiG9w0BAQsFADB6MQswCQYDVQQGEwJV
  SzETMBEGA1UECAwKU29tZS1TdGF0ZTEQMA4GA1UECgwHQWNjYW50bzEQMA4GA1UE
  <full certificate reduced to keep this example short>
  JBe9/l3FuXLjL0PpEdVaO7mlPceL1AlXU/pcnoSM
  -----END CERTIFICATE-----
```

Repeat for the key file (`key.pem`) and CA cert (`ca.pem`), to build a full set of tls properties:

```
helm.tls.enabled: "true"
helm.tls.cacert: |
  -----BEGIN CERTIFICATE-----
  MIIFxzCCA6+gAwIBAgIJANSZZeXuZLszMA0GCSqGSIb3DQEBCwUAMHoxCzAJBgNV
  BAYTAlVLMRMwEQYDVQQIDApTb21lLVN0YXRlMRAwDgYDVQQKDAdBY2NhbnRvMRAw
  <full certificate reduced to keep this example short>
  Z2T2275G1iqFkfbBPbOqNSlIhOxQgx3Mdq764L7kaASX7ElOjfyZS4Xssg==
  -----END CERTIFICATE-----
helm.tls.cert: |
  -----BEGIN CERTIFICATE-----
  MIIFWjCCA0ICCQD5Avb/OJ3QcTANBgkqhkiG9w0BAQsFADB6MQswCQYDVQQGEwJV
  SzETMBEGA1UECAwKU29tZS1TdGF0ZTEQMA4GA1UECgwHQWNjYW50bzEQMA4GA1UE
  <full certificate reduced to keep this example short>
  JBe9/l3FuXLjL0PpEdVaO7mlPceL1AlXU/pcnoSM
  -----END CERTIFICATE-----
helm.tls.key: |
  -----BEGIN RSA PRIVATE KEY-----
  MIIJKAIBAAKCAgEA3GJEBcZg7vTxIlZ9a2fKvi9FxJnn12GvhtvxfXdkdKwNmtds
  <full key reduced to keep this example short>
  sodtxV6twi+hKaLrv33pDGkfIyJM4tkLRzRYGIanRR+NdWFqS+/X9bSvmY8=
  -----END RSA PRIVATE KEY-----
```
