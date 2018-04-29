================
Madcore CLI
================
**************************************************************
Deep Learning & Machine Intelligence Infrastructure Controller
**************************************************************

.. image:: https://travis-ci.org/madcore-ai/cli.svg?branch=master

What is Madcore?
------------------

Madcore is a CLI tool for deployment and auto-configuration of data mining and analytics microservices. It is a Kubernetes-based unmodified KOPS/Minikube installation manager. However, single point of truth is preserved as a unified yaml file called "clusterfile". Clusterfile controls generic aspects of provisioning, deployment, scale and configuration. All KOPS and Kubernetes templates are then populated from input clusterfile.


Install
-------

Mac & Linux install form terminal.

.. code-block:: bash

   pip install madcore


Minikube Environment Prerequisites
----------------------------------

 * Virtual Box
 * Minikube 1.9
 * Local PC 16GB of Ram (minikube is set at 8GB by default)

AWS Environment Prerequisites
-----------------------------

 * VPC in AWS (you will need id)
 * Internet Gateway attached to VPC
 * S3 Storage bucket for KOPS settings


Provision Locally on Minikube or in AWS Cloud
---------------------------------------------

Currently Madcore is tested on Mac and Linux only. We are working on exposing clusterfiles and templates in a better way. By default they install with the python project files location similar to this `lib/python2.7/site-packages/madcore`

.. code-block:: bash

   pip install madcore


Data Mining & Deep Learning Ecosystem
-------------------------------------

Functionality is grouped into instance groups (physically) and into namespaces (logically). Each software deployed here belongs to their respective owners. We do not interfere in containers but make sure that we find best containers for deployment in Kubernetes.

Goal of Madcore is to abstract deployment and configuration of data processing elements and have it available in working state out-of-the-box. This way anyone can start work on their actual problem and not spend time on deployment and configuration of common toolsets.


Deploy Core
-----------

Installation of core elements is a single command. Filenames in range of 100-200. You can comment out any of those installs. By commenting corresponding lines in your aws clusterfile. Registry and metrics elements are optional. You probably want to leave dashboard and ingress setup as everything else maps to it.

.. code-block:: bash

   madcore --install-core

================  =====
Core Stack        Description
================  =====
dashboard         Kubernetes Dashboard
nfs               NFS 4.1 for utilized for Kubernetes persistent volume claims (StatefulSets)
registry2         (optional) docker registry v2
influxdb          InfluxDB for Heapster data
heapster          Kubernetes metrics collector
grafana           Grafana Dashboard pointed at InfluxDB for kube metrics
haproxy-ingress   HAProxy ingress (route external traffic and map to kube services)
ingress-default   default container reporting 404 when hitting anything but mapped endpoints
ingress echo      echo container to test ingress alive
================  =====


Deploy neo4j
------------

Neo4j and Dashboard is in the template file space of 9220-9229. Deploy using command below. Few second later you will have a working dashboard and single pod engine configuration ready to start your tests. Thi deployment is installed onto standard `nodes` instancegroup. This deployment lives its own `neo4j` namespace. It's easy to remove it when you don't require it anymore. It using standard `neo4j:3.1.4-enterprise` containers from docker hub maintainer by neo4j team. It is exposed through ingress and mapped through its own subodmain `neo4j.<yourdomain.com>`

.. code-block:: bash

   madcore --install-neo4j

================  =====
Neo4J Stack       Description
================  =====
engine            Enterprise: neo4j:3.1.4-enterprise (subject to EULA)
ui                Dashboard
================  =====


Deploy kafka
------------

Kafka and Dashboard is in the template file space of 9240-9249. Deploy using command below. Few second later you will have a working dashboard and single pod engine configuration ready to start your tests. Thi deployment is installed onto standard `nodes` instancegroup. This deployment lives its own `kafka` namespace. It's easy to remove it when you don't require it anymore. It is exposed through ingress and mapped through its own subodmain `kafka.<yourdomain.com>` for Yahoo kafka dashboard and `kafka.<yourdomain.com>/rest` for Mailgun Pixy rest ui (grpc is listening internally but not exposed outside)

.. code-block:: bash

   madcore --install-kafka

================  =====
Kafka Stack       Containers
================  =====
zookeeper         solsson/kafka:1.0.1
kafka             solsson/kafka:1.0.1
kafka-manager     solsson/kafka-manager
kafka-pixy        mailgun/kafka-pixy
================  =====


Deploy Elasticsearch / FluentD / Kibana
---------------------------------------

Famous trio optimized for Kubernetes. Elasticsearch exposed through ingress as well as Kibana. Internally FluentD DaemonSets are deployed to ALL nodes and collect all logs from pods stdout along with kubernetes logs and aggregate in ElasticSearch. Deploy this when you have a need. There is a dedicated instance group for ELK so it doesn't collide with any of your other applications.

.. code-block:: bash

   madcore --install-elk

================  =====
Kafka Stack       Containers
================  =====
elasticsearch     docker.elastic.co/elasticsearch/elasticsearch-oss:6.0.0
fluentd           fluent/fluentd-kubernetes-daemonset:v0.12.33-elasticsearch
kibana            docker.elastic.co/kibana/kibana-oss:6.0.0
================  =====


Chat with us on Gitter
----------------------

If you want to try Madcore, make sure you join us on Gitter. We are now focused on building Machine Learning and Ai plugins as well as building Ingress listeners for social media and queueing mechanisms in Spark and Kafka.  All based on Kubernetes. Chat with us now: https://gitter.im/madcore-ai/core

Mailing List
------------

Visit https://madcore.ai to sign up for weekly newsletter on Machine Learning and AI simulations that are now possible with Madcore

Credits
-------

We will be adding a formal Credits file into this project. For now just want to make clear that all registered brands/products remain property of their respective owners.

License
-------

Madcore Project is distributed on MIT License (c) 2016-2017 Madcore Ltd (London, UK) https://madcore.ai
