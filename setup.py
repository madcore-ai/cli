#!/usr/bin/env python
import os
from subprocess import check_output

from setuptools import setup, find_packages

PROJECT = 'madcore'

VERSION = '0.3'


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
    long_description = open('README.md', 'rt').read()
except IOError:
    long_description = ''

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name=PROJECT,
    version=VERSION,

    description='Madcore Core CLI - Deep Learning & Machine Intelligence Infrastructure Controller',
    long_description=long_description,

    author='Peter Styk',
    author_email='humans@madcore.ai',

    url='https://github.com/madcore-ai/cli',
    download_url='https://github.com/madcore-ai/cli/tarball/master',
    keywords=['aws', 'infrastructure'],
    classifiers=['Development Status :: 3 - Alpha',
                 'License :: OSI Approved :: MIT License',
                 'Programming Language :: Python :: 2.7',
                 'Intended Audience :: Developers',
                 'Environment :: Console',
                 ],

    platforms=['Any'],

    scripts=[],

    provides=[],
    # TODO@geo get this from requirements.txt
    install_requires=required,

    namespace_packages=[],
    packages=find_packages(),
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'madcore = madcore.madcore:main'
        ],
        'madcorecli.app': [
            'complete = cliff.complete:CompleteCommand',
            'configure = madcore.cmds.configure:Configure',
            'stacks = madcore.cmds.stacks:Stacks',
            'create = madcore.cmds.create:Create',
            'delete = madcore.cmds.delete:Delete',
            'followme = madcore.cmds.followme:Followme',
            'endpoints = madcore.cmds.endpoints:Endpoints',
            'selftest = madcore.cmds.selftest:SelfTest',
            'registration = madcore.cmds.registration:Registration',
        ],
    },
    data_files=[
        (os.path.join(os.path.expanduser("~"), '.madcore'), [])
    ],

    zip_safe=False,
)
