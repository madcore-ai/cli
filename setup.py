#!/usr/bin/env python

PROJECT = 'madcore'

# Change docs/sphinx/conf.py too!
VERSION = '0.1'

from setuptools import setup, find_packages

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
    keywords = ['aws', 'infrastructure'],
    classifiers=['Development Status :: 3 - Alpha',
                 'License :: OSI Approved :: MIT License',
                 'Programming Language :: Python :: 2.7',
                 'Intended Audience :: Developers',
                 'Environment :: Console',
                 ],

    platforms=['Any'],

    scripts=[],

    provides=[],
    install_requires=['cliff','boto3','urllib3'],

    namespace_packages=[],
    packages=find_packages(),
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'madcore = madcore.madcore:main'
        ],
        'madcore': [
            'stack describe = madcore.stack:StackDescribe',
            'core followme = madcore.core:CoreFollowme',
        ],
    },

    zip_safe=False,
)
