#!/usr/bin/env python
from __future__ import unicode_literals, print_function
from subprocess import check_output
from setuptools import setup, find_packages
from setuptools.dist import Distribution
#from madcore.cmd import Cmd
import subprocess
import sys
import pkg_resources


#class BinaryDistribution(Distribution):
#
#    def is_pure(self):
#        return False


def get_semantic_version():
    global VERSION
    try:
        return pkg_resources.get_distribution("madcore").version
    except:
        proc1 = subprocess.Popen("git describe --tags", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out = proc1.communicate()

        if proc1.returncode != 0:
            sys.stdout.write("madcore must install from cloned folder. make sure .git folder exists\n")
            sys.stdout.write(out[1])
            raise SystemExit(32)

        v = out[0].replace('\n','')

        if v.startswith('v.'):
            v = v[2:]
        elif v.startswith('v'):
            v = v[1:]
        li = v.split('.')
        lii = li[1].split('-')
        if len(lii) == 3:
            v = '{0}.{1}.{2}'.format(li[0],lii[0],lii[1])
        else:
            v = '{0}.{1}'.format(li[0], li[1])
        return v


VERSION = get_semantic_version()
PROJECT = 'madcore'

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
    license='MIT',

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

    #scripts=[],

    #provides=[],
    install_requires=[
        'termcolor==1.1.0',
        'Jinja2==2.9.6',
        'yamlordereddictloader==0.4.0',
        'pyOpenSSL==16.2.0',
        'urllib3==1.22',
        'prettytable==0.7.2',
        'requests==2.18.4',
    ],

    #namespace_packages=[],
    packages=find_packages(),
    #packages=['madcore'],
    include_package_data=True,
    #scm_version_options={
    #    'write_to_template': '{tag}+dYYYMMMDD',
    #    'write_to' : 'version.py'
    #},

    #packages = ['.','templates','static','docs'],

    #package_data={'.git':['*']},
    #distclass=BinaryDistribution,
    zip_safe=False,

    entry_points={
        'console_scripts': [
            'madcore = madcore.madcore:main'
        ]
    }
)
