def checkReady(keg, props, resultBuilder, log, *args, **kwargs):
    found, helm_release = keg.helm_releases.get("hello-" + props['system_properties']['resource_id_label'], props['namespace'])
    