# Deployment Locations

A deployment location must be provided to an infrastructure request to indicate the Kubernetes environment to be used. The deployment location will be managed by the Lifecycle Manager and Brent but must have particular properties to be successfully used by this driver.

# Properties

The following properties are supported by the driver:


| Name            | Default | Required                           | Detail                                                                                                                     |
| --------------- | ------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| clientConfig      | -       | Y                                  | A multiline string version of the kubectl config file used to access the target cluster (see more details below) |
| crdApiVersion | apiextensions.k8s.io/v1beta1    | N                                  | To deploy custom resource types in Kubernetes the CRD API version is required. Only update this if a later release of Kubernetes upgrades the API version |
| defaultObjectNamespace | default | N | Sets the default namespace used when deploying Kubernetes objects on a create request. This value is only used when the object does not have a specified namespace in the metadata section of it's configuration |
| driverNamespace     | Value of defaultObjectNamepsace/default_object_namespace      | N | Sets the namespace to be used by the driver for any Kubernetes objects it creates for management purposes |
| helmVersion     | 2.8.2      | N | Determines the helm client version to use when deploying helm charts (allowed values: 2.8.2, 2.16.7) |

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

