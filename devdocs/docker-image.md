# Docker Image

The Docker image for this driver includes the following features:

- Installs the driver from a `whl` file created with standard Python setuptools
- Runs the `kubedriver` command to start the driver application with a uwsgi container (standard for Python production applications)
- Supports installing a development version of Ignition from a `whl` file
- Supports configuring the exposed port for the driver at both build and runtime
- Supports configuring the uWSGI container implementation used at both build and runtime (also includes configuring the number of processes and threads used by uWSGI container)

## Build Docker Image

This guide shows you how to build the Docker image for testing 

### 1. Build Python Wheel

This requires `setuptools` and `wheel` to be installed:

```
python3 -m pip install --user --upgrade setuptools wheel
```

Run the `setup.py` script at the root of the project to produce a whl (found in `dist/`):

```
python3 setup.py bdist_wheel
```

### 2. Build Docker Image

This requires `docker` to be installed and running on your local machine.

Move the whl now in `dist` to the `docker/whls` directory (create the `whls` directory if it does not exist. Ensure no additional whls are in this directory if it does)

```
rm -rf ./docker/whls
mkdir ./docker/whls
cp dist/kubedriver-<release version number>-py3-none-any.whl docker/whls/
```

Navigate to the Docker directry and build the image. Tag with the release version number.

```
cd docker
docker build -t kubedriver:<release version number> .
```