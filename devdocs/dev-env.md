# Dev Env

These docs help you get a full dev environment setup for working on this driver, with potentially a development version of the Ignition framework.

## Install Python

You need Python3.9+ and pip. Install those according to the instructions for your operating system. 

For Ubuntu, you can do this:

```
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.9
sudo apt install python3.9-distutils
sudo apt install libpython3.9-dev
python3.9 --version
```

If you run `python3 --version` and get a different version then you need to do the following, replacing `3.6` with the major and minor version you have:

```
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 2
sudo update-alternatives --config python3
```

Enter 2 for python3.9

For pip, use:

```
sudo apt install python3-pip
```

## Install base libraries

Once you have Python, you should upgrade and install the following:

```
python3 -m pip install --upgrade pip setuptools wheel virtualenv
```

## Create Virtual Environment

Virtual environments keep your python libraries isolated so it's best to create one for each python project you work on. Create one for this driver project in this repo with the name of `env`, as this is already in the `.gitignore` file so won't be added on commits.

```
python3 -m virtualenv env
```

Activate the environment:

```
source env/bin/activate
```

For windows:

```
env\Scripts\activate.bat
```

## Install Ignition

You may need a development version of [Ignition](https://github.com/IBM/ignition), (check `ansibledriver/pkg_info.json`. If `ignition-version` includes a `.devX` version, then you do). You should install the development version of Ignition into your environment before installing the driver.

Clone the [Ignition](https://github.com/IBM/ignition) project and install it into your virtualenv:

```
python3 -m pip install --editable ~/my-git-repos/ignition
```

## Install the driver

Use setuptools to install the driver and it's dependencies. It's best to use `--editable` so changes you make to the driver are picked up (note: if you add new dependencies you will need to re-install):

```
python3 -m pip install --editable .
```

## Setup Helm

If you intend to run the driver locally and deploy Resources with Helm charts, you will need the Helm client libraries installed (this is because the driver will start subprocesses to call Helm on the command line). 

On ubuntu, you can do this using the same script used by the Dockerfile to bundle Helm into the image:

```
chmod u+x ./docker/setup-helm.sh
./docker/setup-helm.sh 3.12.3
```

Include as many versions as you need separated by spaces. Ensure the versions exist on the [Helm Github releases page](https://github.com/helm/helm/releases).

For other systems, look at the contents of the script to see the steps and adapt them for your OS. In pseudo terms, you need to:

- Download the version of the Helm you want
- Extract the archive 
- Copy the `helm` binary included in the archive to any bin directory on your PATH
- Rename the `helm` binary to `helm$version` e.g helm3.12.3
- Run `helm3.12.3 --help` to verify this has worked

## Install the build dependencies

If you want to use the `build.py` script to automate builds, you should install the requirements:

```
python3 -m pip install -r build-requirements.txt
```

Check the help option for build.py to see what it can do:

```
python3 build.py --help
```

`--release` is reserved for maintainers capable of building a release.
