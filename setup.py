#!/usr/bin/env python
from __future__ import unicode_literals, print_function

from subprocess import check_output

from setuptools import setup, find_packages

PROJECT = 'madcore'

VERSION = '0.4.2'


def format_version(version):
    fmt = '{tag}.{commitcount}+{gitsha}'
    parts = version.split('-')
    assert len(parts) in (3, 4)
    dirty = len(parts) == 4
    tag, count, sha = parts[:3]
    if count == '0' and not dirty:
        return tag
    return fmt.format(tag=tag, commitcount=count, gitsha=sha)


def get_git_version():
    global VERSION
    git_version_command = 'git describe --tags --long'
    try:
        VERSION = check_output(git_version_command.split()).decode('utf-8').strip()
        VERSION = format_version(VERSION)
    except:
        pass


get_git_version()

try:
    long_description = open('README.rst', 'rt').read()
except IOError:
    long_description = ''

setup(
    name=PROJECT,
    version=VERSION,

    description='Madcore Core CLI - Deep Learning & Machine Intelligence Infrastructure Controller',
    long_description=long_description,

    author='Peter Styk',
    author_email='humans@madcore.ai',

    url='https://github.com/madcore-ai/cli',
    download_url='https://github.com/madcore-ai/cli/tarball/master',
    keywords=['aws', 'infrastructure', 'kubernetes', 'cluster', 'machine learning', 'gpu'],
    classifiers=['Development Status :: 3 - Alpha',
                 'License :: OSI Approved :: MIT License',
                 'Programming Language :: Python :: 2.7',
                 'Intended Audience :: Developers',
                 'Environment :: Console',
                 ],

    platforms=['Any'],

    scripts=[],

    provides=[],
    install_requires=[
        'six>=1.9.0',
        'cliff==2.4.0',
        'boto3==1.4.4',
        'urllib3==1.20',
        'python-jenkins==0.4.13',
        'requests==2.12.5',
        'questionnaire==1.1.0',
        'pyfiglet==0.7.5',
        'Pygments==2.2.0',
        'jinja2==2.9.4'
    ],

    namespace_packages=[],
    packages=find_packages(),
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'madcore = madcore.cli:main'
        ],
        'madcorecli.app': [
            'configure = madcore.cmds.configure:Configure',
            'stacks = madcore.cmds.stacks:Stacks',
            'create = madcore.cmds.create:Create',
            'destroy = madcore.cmds.destroy:Destroy',
            'followme = madcore.cmds.followme:Followme',
            'endpoints = madcore.cmds.endpoints:Endpoints',
            'selftest = madcore.cmds.selftest:SelfTest',
            'registration = madcore.cmds.registration:Registration',
            'up = madcore.cmds.up:MadcoreUp',
            'halt = madcore.cmds.halt:MadcoreHalt',
            'ssh = madcore.cmds.ssh:MadcoreSSH',
            'status = madcore.cmds.status:Status',
            'plugin list = madcore.cmds.plugins.list:PluginList',
            'plugin install = madcore.cmds.plugins.install:PluginInstall',
            'plugin remove = madcore.cmds.plugins.remove:PluginRemove',
            'plugin status = madcore.cmds.plugins.status:PluginStatus'
        ],
    },
    zip_safe=False,
)
