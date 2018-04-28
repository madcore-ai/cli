================
Madcore Core CLI
================
**************************************************************
Deep Learning & Machine Intelligence Infrastructure Controller
**************************************************************

.. image:: https://travis-ci.org/madcore-ai/cli.svg?branch=master

What is Madcore
------------------

Madcore CLI is a tool for auto-configuration of deployment of Madcore Core. A small, private instance in AWS where you can experiment with Kubernetes, Auto Scaling Groups based on Spot Instances, Spark, Cuda7, Deep Learning and AI frameworks.

It allows you quickly run data mining and data processing tasks, scale clusters as needed, auto-save config and data. Destroy everything when not used (small backup saved on S3), restore when you're back to working mood. Utilizing Auto Scaling Groups and Spot Instances so you can work at fraction of Amazon AWS on-demend pricing. Madcore is perfect choice if you want to forget about setting up containerized infrastructure and just focus on your work.

Install
------------------

.. code-block:: bash

   pip install madcore

Runtime Prerequesites
---------------------

 * Create AWS IAM User
 * Run “aws configure” to setup key, secret and default region will be used by madcore
 * Create AWS EC2 Key-Pair (or reuse existing, remember keys are per region)
 * Create or get your Bitbucket user ready
 * Make sure you have at least one Team in Bitbucket (even if only you)
 * run “madcore” on your terminal

1st Time Run
------------------

First time you run "madcore" the cli will required an extra authorization to make sure your subodmain is properly delegated on "madcore.cloud" or "devopshosted.com" domain. For example if you have a Bitbucket team "TheATeam" you will have a choice to mount it as a subdomain on top of either "madcore.cloud" or "devopshosted.com" domain. Example: "theateam.madcore.cloud"  You will recieve full DNS delegation for the zone and all future deployments and endpoints will have services mapped on that subdomain. For example  "kubedash.theateam.madcore.cloud" or "jenkins.theateam.madcore.cloud"

madcore configuration will then automatically proceed to deploy the following madcore cloud formation stacks

================  =====
Stack Name         Description
================  =====
Madcore-NET        Isolated VPC, Subnets, Integrent Gateway only for madcore
Madcore-FollowMe   SG autoconfigured based on your public ip address
Madcore-S3         Your private S3 bucket used by Core nodes
Madcore-DNS        Your madcore subdomain, delegated by Madcore
Madcore-Core       Core Instance, t2.small or m3.medium
================  =====

Automated Installation and Configuration
----------------------------------------

With exception of few initial questions, entire process is fully automated. At the end Madcore will reconfigure HAproxy 443 (SSL) entry point and run first jenkins job (madcore.registration) which will obtain Let's Encrypt certificate and connect everything together. Installation takes about 20 minutes. End result is you having your own, fully private (only from your ip) access to the following:

.. code-block:: bash

  https://kubedash.theateam.madcore.cloud (Kubernetes Master Dashboard)
  https://jenkins.theateam.madcore.cloud (Jenkins with Madcore DSL Jobs)
  https://grafana.theateam.madcore.cloud (Grafana Metrics Visualization)
  https://influxdb.theateam.madcore.cloud (Influx DB storage for Grafana)
  https://registry.theateam.madcore.cloud (Docker Registry)
  https://kubeapi.theateam.madcore.cloud (Kubernetes API)

Above is a list of exposed endpoints only.


CLI Command: configure
----------------------

Configure is triggered when you first time run "madcore"  it starts by creating ~/.madcore folder and config file that stores information used for auto configuration. Configure builds network, storage, dns and core instance as described above. It also registers ssl certificate or restores existing certificate. When configure was run before and Core was terminated with Destroy command, configure will run unattended (because config has all the answers)

CLI Command: destroy
--------------------

Core installation is done through CloudFormation stacks mentioned above so can be completely removed when not required. Two stacks survive destructions, DNS and S3.  Dns is valid delegated subdomain. S3 bucket is used for ssl certificates and redis backup/restore.

CLI Command: halt
-----------------

Stops core instance. When not used, stopped instance is not charged EC2 charges.

CLI Command: up
-----------------

Starts core instance.

CLI Command: ssh
-----------------

Automatically connects to core instance. Uses private key path you specified during configure step. And core should have been created using matching public EC2 key selected during configure step.

CLI Command: plugin list
------------------------

List currently available community Madcore plugins.

=============  =====
Plugin Name    Description
=============  =====
flasker        Example. Build simple flask python application into Docker Container, Store container in local private docker registry, create kubernetes pod with new docker image, deploy pod into kubernetes directly from local private docker registry
flasker-hub    Example. Use existing Docker Hub image, create kubenretes pod, deploy pod into kubernetes directly from public Docker Hub
k8s            Extend Kubernetes Nodes into Auto Scaling Group using Spot Instances
spark          Install Spark on Kubernetes, Extend Kubernetes Nodes and dedicate them to Spark using Auto Scaling Group and based on Spot Instances
gpu            Amazon Ai AMI's running Cuda7 Nvidia GPU framework, DeepLearning4j deployments are delivered directly into instance (no containerization) Auto Scaling Group using Spot Instances
=============  =====

CLI Command: plugin install <name>
----------------------------------

Extends your existing Core with functionality described by the plugin.


CLI Command: plugin delete <name>
---------------------------------

Removes plugin and all traces of clusters from the Core (with exception of data saved to madcore private S3 bucket directly from instance/node/pod)

CLI Commands added by plugin
----------------------------

Each plugin can (but doesn't have to) extend CLI with new commands. For example in case of spark it can be either python or java spark code that will perform functions specific to spark cluster.

Chat with us on Gitter
----------------------

If you want to try Madcore, make sure you join us on Gitter. We are now focused on building Machine Learning and Ai plugins as well as building Ingress listeners for social media and queueing mechanisms in Spark and Kafka.  All based on Kubernetes. Chat with us now: https://gitter.im/madcore-ai/core

Mailing List
-----------------

Visit https://madcore.ai to sign up for weekly newsletter on Machine Learning and AI simulations that are now possible with Madcore

Credits
-----------------

We will be adding a formal Credits file into this project. For now just want to make clear that all registered brands remain property of their respective owners.

License
-----------------

Madcore Project is distributed on MIT License (c) 2016-2017 Madcore Ltd (London, UK)
