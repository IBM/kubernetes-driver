# Build Helm Chart

To build the Helm chart you will need to install Helm and initialised it (e.g. `helm init --client-only`).

Build the chart with the package command:

```
helm package helm/kubedriver
```

The command will print the location of the generated `.tgz` Helm package.