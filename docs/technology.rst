==========
Technology
==========

.. contents:: Table of contents
    :depth: 1
    :local:

Docker Container is the common denominator and this is where your code ends up.
Docker Registries holds containers. Kubernetes is managing runtime of containers and Kubernetes Charts (Helm)
are persisting details of infrastructure required to launch your container (scaling, storage, run types,
variables, secrets). AWS with Ubuntu Xenial infrastructure is used to provide flexible organization of
Kubernetes layer. Madcore focus is within Kubernetes realm primarily. Cloud and OS
layer was required since Madcore concept is surrounded by infrastructure elements, however as more cloud providers
offer Kubernetes-As-Service, we will be able to attach Madcore Project to any of them providing they meet
project requirements. In what seems an unlimited amount of choices on how to do this we selected one Cloud and
one OS to stay in focus of mission statement. Below is an incomplete list of credits:


Containers Selection
--------------------

* Kubernetes containerized by GCE
* InfluxDB
* Grafana
* Lego


Cloud Technology Selection
--------------------------

* `Amazon Web Services <https://aws.amazon.com>`_
* EC2
* S3
* IAM
* Cloud Formation
* Instance Profiles
* Route53


Bare OS Technology Selection
----------------------------

* Ubuntu Xenial 16.04
* Docker and Docker Registry
* Jenkins
* Habitat
* Redis
* HAProxy
* Let's Encrypt