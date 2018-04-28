#!/usr/bin/env python
from __future__ import unicode_literals, print_function
from subprocess import check_output
from setuptools import setup, find_packages


PROJECT = 'madcore'


try:
    long_description = open('README.rst', 'rt').read()
except IOError:
    long_description = ''

setup(
    use_scm_version={"root": ".", "relative_to": __file__},
    setup_requires=['setuptools_scm', 'setuptools_scm_git_archive'],

    name=PROJECT,
    version=find_version("madcore", "__init__.py"),

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

    #scripts=[],

    #provides=[],
    install_requires=[
        'termcolor==1.1.0',
        'Jinja2==2.9.6',
        'yamlordereddictloader==0.1.1',
        'pyOpenSSL==16.2.0',
        'urllib3==1.22',
        'prettytable==0.7.2',
        'requests==2.18.4',
        'Fabric==1.13.2',
        'setuptools_scm==2.0.0',
        'setuptools-scm-git-archive==1.0',
    ],

    #namespace_packages=[],
    #packages=find_packages(),
    packages=['madcore'],
    include_package_data=True,
    zip_safe=False,

    entry_points={
        'console_scripts': [
            'madcore = madcore.madcore:main'
        ]
    }
)
