#!/usr/bin/env python
import os

from setuptools import setup, find_packages

PROJECT = 'madcore'

# Change docs/sphinx/conf.py too!
VERSION = '0.3'

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
