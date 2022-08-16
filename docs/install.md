# Install to Kubernetes

This section details how to install the driver into a Kubernetes environment with Helm. 

**Note:** The Kubernetes environment you install into does **NOT** have to be the same Kubernetes deployment location for the Resources it manages.

## Prerequisites

To complete the install you will need a Kubernetes cluster.

You will also need a controller machine (can be one of the Kubernetes cluster nodes) to perform the installation from. This machine must have the Helm CLI tool installed with access to your cluster.

## Installation

### Obtain Helm Chart

Download the Helm chart from your usual release channel e.g. [Github](https://github.com/IBM/kubernetes-driver/releases).

### Configure

You may view the complete set of configurable values of the chart with Helm:

```
helm inspect values kubedriver-<version>.tgz
```

A list of the most common configuration options has also been included as an [appendix](#appendix-a-configuration-values) to this section.

The driver has a dependency on Kafka, which it uses to send response messages back to LM. Therefore it must be installed with access to the same shared Kafka cluster as your Lifecycle Manager.

kafka host value must be set as follows, in values.yaml file of the helm package, depending on the CP4NA versions:

* For pre CP4NA v2.3, the kafka host must be iaf-system-kafka-bootstrap

* For CP4NA v2.3/v2.3+, the kafka host must be cp4na-o-events-kafka-bootstrap  

By default, the driver will attempt to connect to Kafka with the address `cp4na-o-events-kafka-bootstrap:9092`.

If you need to set a different address (or configure any of the other values of the Helm chart) you may do so by creating a custom values file.

```
touch custom-values.yml
```

In this file add any values you wish to override from the chart. For example, to change the Kafka address, add the following:

```
app:
  config:
    override:
      messaging:
        connection_address: "myhost:myport"
```

You will reference the custom-values.yml file when installing the chart with Helm.

### Install

Install the chart using the Helm CLI, adding any custom values file if created.

```
helm install kubedriver-<version>.tgz --name kubedriver -f custom-values.yml
```

The driver runs with SSL enabled by default. The installation will generate a self-signed certificate and key by default, adding them to the Kubernetes secret "kubedriver-tls". To use a custom certificate and key in your own secret, override the properties under "apps.config.security.ssl.secret".

### Confirm

You can confirm the driver is working accessing: ```http://<kubernetes-node-ip>:31684/management/health```

Onboard the driver with [LMCTL v2.5.0+](https://github.com/IBM/lmctl):
```
kubectl get secret kubedriver-tls -o 'go-template={{index .data "tls.crt"}}' | base64 -d > kubedriver-tls.pem

lmctl resourcedriver add --type kubernetes --url https://kubedriver:8294 --certificate kubedriver-tls.pem dev-env 
```

# Appendix A - Configuration Values

## Helm Configuration

The following table lists configurable parameters of the chart:

| Parameter | Description | Default |
| --- | --- | --- |
| docker.image | Name of the image for the driver (may include docker registry information) | accanto/kubedriver |
| docker.version | Image tag to deploy | <version of the chart> |
| docker.imagePullPolicy | Image pull policy | IfNotPresent |
| app.replicas | Number of instances of the driver to deploy | 1 |
| app.config.log.level | Level of log messages output by the driver | INFO |
| app.config.env | Environment variables to be passed to the driver | (See below) |
| app.config.env.LOG_TYPE | Log format (leave as logstash) | logstash |
| app.config.env.WSGI_CONTAINER | WSGI container implementation used by the driver | gunicorn |
| app.config.env.NUM_PROCESSES | Number of threads per process | 2 |
| app.config.override | Map to set [Application Configuration)[#app-configuration] properties | See connection_address below and [Application Configuration)[#app-configuration] properties |
| app.config.override.message.connection_address | Kafka address. Default set to address of Kafka installed as standard with LM | cp4na-o-events-kafka-bootstrap:9092 |
| app.config.security.ssl.enabled | Enabled/disable SSL | True |
| app.config.security.ssl.secret.name | Name of the secret containing the SSL certificate for the non-host based access | kubedriver-tls |
| app.config.security.ssl.secret.generate | If True, the Helm chart installation will generate a new SSL key with a self-signed certificate | True |
| app.affinity | Affinity settings | A pod anti-affinity rule is configured to inform Kubernetes it is preferable to deploy the pods on different Nodes |
| app.tolerations | Tolerations for node taints | [] |
| app.resources | Set requests and limits to CPU and memory resources | {} |
| service.type | Type of Service to be deployed | NodePort |
| service.nodePort | NodePort used to expose the service | 31684 |

## Application Configuration

The following table lists configurable parameters of the Application, that may be specified in the `app.config.override` value of the Helm chart:

| Parameter | Description | Default |
| --- | --- | --- |
| application.port | Port the application runs on (internal access only) | 8294 | 
| messaging.connection_address | Kafka address | cp4na-o-events-kafka-bootstrap:9092 |
