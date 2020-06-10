#!/bin/sh

set -e

rm -rf helmtmp
mkdir helmtmp
cd helmtmp
for version in $1
do
    wget https://get.helm.sh/helm-v$version-linux-amd64.tar.gz 
    tar -xvzf helm-v$version-linux-amd64.tar.gz 
    cp linux-amd64/helm /usr/local/bin/helm$version
    helm$version --help
    rm -rf linux-amd64
    rm helm-v$version-linux-amd64.tar.gz 
done

cd ..
rm -rf helmtmp