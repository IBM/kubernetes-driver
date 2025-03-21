def checkReady(keg, props, resultBuilder, log, *args, **kwargs):
    namespace = props['chartNamespace']
    releaseName = "hello-" + props['system_properties']['resource_id_label']

    releaseFound, helmRelease = keg.helm_releases.get(releaseName, namespace)
    if not releaseFound:
        resultBuilder.failed("Helm release not found")
        return

    deploymentFound, deployment = helmRelease.objects.get('apps/v1', 'Deployment', releaseName + "-nginx", namespace=namespace)
    if not deploymentFound:
        resultBuilder.failed("Deployment not found")
        return


    if 'readyReplicas' in deployment['status'] and deployment['status']['readyReplicas'] > 0:
        resultBuilder.ready()
    else:
        resultBuilder.notReady()
        