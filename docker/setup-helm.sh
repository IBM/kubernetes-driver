#!/bin/bash

set -e

mkdir helm
cd helm
for version in $SUPPORTED_HELM_VERSIONS
do
    wget https://get.helm.sh/helm-v$version-linux-amd64.tar.gz 
    tar -xvzf helm-v$version-linux-amd64.tar.gz 
    cp linux-amd64/helm /usr/local/bin/helm$version
    helm$version --help
    rm -rf linux-amd64
    rm helm-v$version-linux-amd64.tar.gz 
done