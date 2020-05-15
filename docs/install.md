# Install to Kubernetes

This section details how to install the VIM driver into a Kubernetes environment with Helm. 

**Note:** The Kubernetes environment you install into does **NOT** have to be the same Kubernetes deployment location for the Resources it manages.

## Prerequisites

To complete the install you will need a Kubernetes cluster with:

You will also need a controller machine (can be one of the Kubernetes cluster nodes) to perform the installation from. This machine must have the Helm CLI tool installed and initialised with access to your cluster.

## Installation

### Obtain Helm Chart

Download the Helm chart from your usual release channel.

### Configure

You may view the complete set of configurable values of the chart with Helm:

```
helm inspect values kubedriver-<version>.tgz
```

A list of the most common configuration options has also been included as an [appendix](#ppendix-a-configuration-values) to this section.

The driver has a dependency on Kafka, which it uses to send response messages back to LM. Therefore it must be installed with access to the same shared Kafka cluster as your Lifecycle Manager. 

By default, the driver will attempt to connect to Kafka with the address `foundation-kafka:9092`. This is suitable if the driver is being installed into the same namespace as a standard installation of the Lifecycle Manager since its foundation services include Kafka.

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

### Obtain Docker Image

By default the chart expects the image to be available on the local docker system under the tag `kubedriver:<version>`

```
docker:
  image: kubedriver
  version: <version>
```

If you have the Docker image available in a registry then you must update the values file with the full path to the image:

```
docker:
  image: myregistry:registryport/kubedriver-<version>
```

If you have instead saved the image and loaded into the system with docker CLI commands, check the path name of your image with `docker images | grep kubedriver`. If the image is tagged as `kubedriver:<version>`, you do not need to make changes to the values. However, if the image has a registry path infront of it you should tag the image to remove the registry or update your custom values file with the full path as displayed in the list.

### Install

Install the chart using the Helm CLI, adding any custom values file if created.

```
helm install kubedriver-<version>.tgz --name kubedriver -f custom-values.yml
```

The driver runs with SSL enabled by default. The installation will generate a self-signed certificate and key by default, adding them to the Kubernetes secret "kubedriver-tls". To use a custom certificate and key in your own secret, override the properties under "apps.config.security.ssl.secret".

### Confirm 

You can confirm the driver is working by accessing the Swagger UI included to render the API definitions.

Access the UI at `https://your_host:31684/api/infrastructure/ui` e.g. [`http://localhost:31684/api/infrastructure/ui`](http://localhost:31684/api/infrastructure/ui)

To onboard the driver follow the instructions on [Service Lifecycle Manager](http://servicelifecyclemanager.com/2.1.0/user-guides/resource-engineering/drivers/onboarding/). Note: the Kubedriver does not currently install with SSL so you should use a `http://` based address and you do not need to provide certificate when onboarding.

# Appendix A - Configuration Values

## Helm Configuration

The following table lists configurable parameters of the chart:

| Parameter | Description | Default |
| --- | --- | --- |
| docker.image | Name of the image for the driver (may include docker registry information) | kubedriver |
| docker.version | Image tag to deploy | <version of the chart> |
| docker.imagePullPolicy | Image pull policy | IfNotPresent |
| app.replicas | Number of instances of the driver to deploy | 1 |
| app.config.log.level | Level of log messages output by the driver | INFO |
| app.config.env | Environment variables to be passed to the driver | (See below) |
| app.config.env.LOG_TYPE | Log format (leave as logstash) | logstash |
| app.config.env.WSGI_CONTAINER | WSGI container implementation used by the driver | gunicorn |
| app.config.env.NUM_THREADS | Number of threads per process | 2 |
| app.config.override | Map to set [Application Configuration)[#app-configuration] properties | See connection_address below and [Application Configuration)[#app-configuration] properties |
| app.config.override.message.connection_address | Kafka address. Default set to address of Kafka installed as standard with LM | foundation-kafka:9092 |
| app.affinity | Affinity settings | A pod anti-affinity rule is configured to inform Kubernetes it is preferable to deploy the pods on different Nodes |
| app.tolerations | Tolerations for node taints | [] |
| app.resources | Set requests and limits to CPU and memory resources | {} |
| service.type | Type of Service to be deployed | NodePort |
| service.nodePort | NodePort used to expose the service | 31684 |
| ingress.enabled | Flag to disable/enable creation of an Ingress rule for external access | true |
| ingress.host | Hostname on the Ingress rule | kubedriver.lm |

## Application Configuration

The following table lists configurable parameters of the Application, that may be specified in the `app.config.override` value of the Helm chart:

| Parameter | Description | Default |
| --- | --- | --- |
| application.port | Port the application runs on (internal access only) | 8294 | 
| messaging.connection_address | Kafka address | foundation-kafka:9092 |