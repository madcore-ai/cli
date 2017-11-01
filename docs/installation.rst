============
Installation
============

.. contents:: Table of contents
    :depth: 1
    :local:

Madcore lives across 5 Github repositories: https://github.com/madcore-ai  All are being actively
developed across many branches. `development` branch is always kept stable and merged into master
when features align at which point a Python PIP package is created. This page will explain on how
to perform a development installation so you have control over branch and commit id's used to pin
your installation into a known working state.


Bitbucket Account
-----------------
Bitbucket account must be a member of at least one Bitbucket team. Team name will be used as unique
name to create your subdomain `https://<bitbucket-team-name>.madcore.cloud` This domain will be
delegated to your account as part of installation. This is required as Madcore will setup all
endpoint on HTTPS/SSL protected endpoints.


AWS Account
-----------
AWS account with access to creating IAM identities and roles. Your instances will assume roles
and be granted permissions to access your S3 buckets where state is persisted between cluster
destructions. Not Madcore and Not any other 3rd party has access to your environment.


Madcore CLI
-----------
CLI must be installed to start the installation. Initial configuration verifies few details
and then unattended installation takes about 30 minutes to complete the process. At that point
you will have your master instance (with firewall open only to your ip address). Accessible
over HTTPS/SSL. You can then securely connect from directly to Jenkins, Grafana and Kubernetes dashboards.

.. code-block:: bash

    pip install madcore