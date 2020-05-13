import json
from setuptools import setup, find_namespace_packages

with open('kubedriver/pkg_info.json') as fp:
    _pkg_info = json.load(fp)

with open("DESCRIPTION.md", "r") as description_file:
    long_description = description_file.read()

setup(
    name='kubedriver',
    version=_pkg_info['version'],
    description='None',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_namespace_packages(include=['kubedriver*']),
    include_package_data=True,
    install_requires=[
        'ignition-framework=={0}'.format(_pkg_info['ignition-version']),
        'kubernetes==11.0.0',
        'python-dateutil==2.8.1',
        'RestrictedPython==5.0.0',
        'gunicorn>=19.9.0,<20.0'
    ],
    entry_points='''
        [console_scripts]
        kubedriver-dev=kubedriver.__main__:main
    ''',
    scripts=['kubedriver/bin/kubedriver-uwsgi', 'kubedriver/bin/kubedriver-gunicorn', 'kubedriver/bin/kubedriver']
)