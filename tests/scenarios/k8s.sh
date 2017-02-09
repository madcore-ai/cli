#!/usr/bin/env bash

# install k8s plugin with input params
madcore plugin install k8s --MinSize=0 --MaxSize=0 --InstanceType=m3.medium --SpotPrice=0.0139 --DesiredCapacity=0

# extend cluster by one node
madcore k8s extend --nodes=1 --InstanceType=m3.medium --SpotPrice=0.0139

# contract cluster by one node
madcore k8s contract --nodes=1

# reset cluster nodes
madcore k8s zero

# remove cluster
madcore plugin remove
