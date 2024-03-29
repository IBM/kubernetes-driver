# Helm

This section describes the `helm` task available to use in the `deploy` section of a deployment strategy (`kegd.yaml` file).

Example:
```
compose:
  - name: Create
    deploy:
      - helm:
          chart: my-chart.tgz
          name: MyRelease
```

## Arguments

### chart

| Mandatory | Default | Templated Value |
| --- | --- | --- | 
| Y | - | Y (see [templating values](#templating-values)) |

The helm chart to install. This should either be the name of a file, from the `Lifecycle/kubernetes/objects` directory of your Resource package, or a valid chart name reference that the target Helm server will understand i.e. with a helm repository followed by a chart name.

### name

| Mandatory | Default | Templated Value |
| --- | --- | --- | 
| Y | - | Y (see [templating values](#templating-values)) |

The name given to the Helm release (`helm install --name <name>`). This needs to be unique, so it's recommended you use a unique property from the Resource (such as it's ID). Bare in mind that Helm release names must be no more than 63 characters and a in the DNS-1035 label format (must consist of lower case alphanumeric characters or '-', start with an alphabetic character, end with an alphanumeric character)

### namespace

| Mandatory | Default | Templated Value |
| --- | --- | --- | 
| N | `defaultObjectNamespace` from the deployment location properties | Y (see [templating values](#templating-values)) |

The namespace to install the Helm chart into (`helm install --namespace <namespace>). 

### values

| Mandatory | Default | Templated Value |
| --- | --- | --- | 
| N | - | Y (see [templating values](#templating-values)) |

The values provided to the installation in order to customise the deployment (`helm install -f <values1> -f <values2>`). This should be a list of names of YAML files (for backwards compatibility a single filename as string is also supported), from the `Lifecycle/kubernetes/helm` directory of your Resource package.

e.g. 
```
compose:
  - name: Create
    deploy:
      - helm:
          chart: test-chart.tgz
          name: r{{ system_properties.resource_id_label }}
          namespace: default
          values: [ "test-values1.yaml", "test-values2.yaml" ]
```

for a directory structure
```
Lifecycle/kubernetes/helm/
├── test-chart.tgz
├── test-values2.yaml
└── test-values1.yaml
```

These files and filenames will be rendered as templates so you may inject properties into them as described in [templating](../user-guide/templating.md)

### setfiles

| Mandatory | Default | Templated Value |
| --- | --- | --- | 
| N | - | Y (see [templating values](#templating-values)) |

The setfiles argument to helm which can be used to pass large config values from external files 
(`helm install --set-file valuesA=valuefileA.yaml,valuesB=valuefileB.yaml`) in order to customise the deployment. This should be a dict of `key:filename` mapping and the files should be from the `Lifecycle/kubernetes/helm` directory of your Resource package.

e.g. 
```
compose:
  - name: Create
    deploy:
      - helm:
          chart: test.tgz
          name: r{{ system_properties.resource_id_label }}
          namespace: default
          setfiles:
               serverA.port.https : "httpsPort.data"
```

for a directory structure
```
Lifecycle/kubernetes/helm/
├── test-chart.tgz
├── test-values2.yaml
├── test-values1.yaml
└── httpsPort.data
```

These files and their keys will be rendered as templates so you may inject properties into these as described in [templating](../user-guide/templating.md)


### immediateCleanupOn

| Mandatory | Default | Templated Value |
| --- | --- | --- | 
| N | Never | N |

Request that the Helm chart is immediately removed at the end of the transition execution (so after ready checks and output extraction).

Possible values for this setting include: 
- Never - the default behaviour, to keep the Helm chart installation until the cleanupOn settings dictate it should be removed 
- Success - the Helm chart installation should be removed after the transition/operation completes successfully 
- Failure - the Helm chart installation should be removed only if the transition/operation fails
- Always - always remove the Helm chart installation at the end of the transition/operation regardless of the result.

A transition is considered "complete" enough to run immediate cleanup after the following phases are complete:

- Removal of any objects that should be removed on this transition/operation
- Deployed objects that are scheduled to on this transition/operation
- Ready check completed successfully 
- Output extraction completed successfully

If a failure occurs during the immediate cleanup, the transition/operation will be marked as failed.

### wait

| Mandatory | Default | Templated Value |
| --- | --- | --- | 
| N | false | N |

If set, will wait until all Pods, PVCs, Services, and minimum number of Pods of a Deployment, StatefulSet, or ReplicaSet are in a ready state before marking the release as successful. It will wait for as long as timeout

### timeout

| Mandatory | Default | Templated Value |
| --- | --- | --- | 
| N | 300 | N |

Time (in seconds) to wait for any individual Kubernetes operation (like Jobs for hooks)

## Templating Values

Example kegd.yaml which uses the value of a `resource_id_sd` system property to build a unique Helm release name:
```
compose:
  - name: Create
    deploy:
      - helm:
          chart: mychart.tgz
          name: r{{ system_property.resource_id_label }}
```

**Note:** the `r` character has been prepended as Helm release names must start with a alphabetic character but the Resource ID may start with a number