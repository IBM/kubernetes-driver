#!/usr/bin/env groovy

String tarquinBranch = "CPNA-1189"

library "tarquin@$tarquinBranch"

pipelinePy {
  pkgInfoPath = 'kubedriver/pkg_info.json'
  applicationName = 'kubedriver'
  releaseArtifactsPath = 'release-artifacts'
  attachDocsToRelease = true
  attachHelmToRelease = true
}
