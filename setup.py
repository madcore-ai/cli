#!/usr/bin/env python
from subprocess import check_output

from setuptools import setup, find_packages

PROJECT = 'madcore'

VERSION = '0.3.6'


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
    install_requires=[
        'six>=1.9.0',
        'cliff==2.4.0',
        'boto3==1.4.3',
        'urllib3==1.19.1',
        'python-jenkins==0.4.13',
        'requests==2.12.4',
        'questionnaire==1.1.0',
        'pyfiglet==0.7.5'
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
        ],
    },
    zip_safe=False,
)
