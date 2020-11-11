# Releasing the Driver

This section describes a recommended method for building and releasing the driver artifacts. 

## 1. Set Versions

1.1 Start by setting the version of the release in `kubedriver/pkg_info.json`:

```
{
    "version": "<release version number>"
}
```

For example:

```
{
    "version": "1.0.0"
}
```

1.2 Ensure the `docker.version` in `helm/kubedriver/values.yaml` includes the correct version number

1.3 Ensure the `version` and `appVersion` in `helm/kubedriver/Chart.yaml` includes the correct version number

1.4 Push all version number changes to Github

```
git add kubedriver/pkg_info.json
git add helm/kubedriver/values.yaml
git add helm/kubedriver/Chart.yaml
git commit -m "Set version numbers for release"
git push origin
```

1.5 Tag the commit with the new version 

```
git tag <release version number>
git push origin <release version number>
```

## 2. Build Python Wheel

This requires `setuptools` and `wheel` to be installed:

```
python3 -m pip install --user --upgrade setuptools wheel
```

2.1 Run the `setup.py` script at the root of the project to produce a whl (found in `dist/`):

```
python3 setup.py bdist_wheel
```

## 3. Package Docs

3.1 Create a TAR version of the docs directory:

```
tar -cvzf kubedriver-<release version number>-docs.tgz docs/ --transform s/docs/kubedriver-<release version number>-docs/
```
On a Mac:
```
tar -cvz -s '/docs/kubedriver-<release version number>-docs/' -f kubedriver-<release version number>-docs.tgz docs/
```
The TAR will be created in the root directory of the project

## 4. Build Docker Image

This requires `docker` to be installed and running on your local machine.

4.1 Move the whl now in `dist` to the `docker/whls` directory (create the `whls` directory if it does not exist. Ensure no additional whls are in this directory if it does)

```
rm -rf ./docker/whls
mkdir ./docker/whls
cp dist/kubedriver-<release version number>-py3-none-any.whl docker/whls/
```

4.2 Navigate to the Docker directry and build the image. Tag with the release version number. Ensure the name of the image is the default name expected in `helm/values.yaml`

```
cd docker
docker build -t kubedriver:<release version number>
```

## 5. Build Helm Chart

This requires the Helm CLI tool to be installed on your machine

5.1 Package the helm chart

```
helm package helm/kubedriver
```

## 6. Release artifacts

Release the artifacts through your normal release channels. We recommend:

- Creating a release on Github and attach the:
    - helm chart tgz
    - docs TAR file
- Push the docker image to a registry or docker hub if open source (alternatively build a TAR of your image with `docker save` and attach it to the Github release)

## 7. Set next development version

7.1 Set the version of the next development version in `kubedriver/pkg_info.json`:

```
{
  "version": "<next development version number>"
}
```

7.2. Update the `docker.version` in `helm/kubedriver/values.yaml` to the next development version number.

7.3. Update the `version` and `appVersion` in `helm/kubedriver/Chart.yaml` to the next development version number.

7.4 Push version number changes to Github

```
git add kubedriver/pkg_info.json
git add helm/kubedriver/values.yaml
git add helm/kubedriver/Chart.yaml
git commit -m "Set next development version"
git push origin
```
