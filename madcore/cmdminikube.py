"""
MIT License

Copyright (c) 2016-2018 Madcore Ltd

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from static import Static
from cmd import Cmd
import subprocess
import os
import sys
import localtemplate


class Minikube(object):
    settings = None

    def __init__(self, in_settings):
        self.settings = in_settings

    def config_vm_virtualbox(self):
        name = "Minikube Configure to use Virtualbox"
        cmd = "minikube config set vm-driver virtualbox"
        Static.msg(name, '.')
        Cmd.local_run_long(name, cmd)

    def start(self):
        name = "Minikube Start"
        cmd = "minikube start --insecure-registry localhost:5000 --memory 6144 --kubernetes-version={0}".format(self.settings.provision.kubernetesVersion)
        Static.msg(name, '.')
        Cmd.local_run_realtime(name, cmd)

    def delete(self):
        name = "Minikube Delete"
        cmd = "minikube delete"
        Static.msg(name, '.')
        Cmd.local_run_realtime(name, cmd)

    def confirm_started(self):
        name = "Minikube Confirm Started"
        cmd = "until kubectl get serviceaccount -n kube-system | grep -m 1 'default'; do sleep 1; done"
        Static.msg(name, '.')
        Cmd.local_run_realtime(name, cmd)

    def is_minikube_in_hosts(self):
        name = "Is minikube.local in hostsfile"
        cmd = "grep -q 'minikube.local' /etc/hosts"
        is_present = Cmd.local_run_return_bool(name, cmd)
        Static.msg(name, is_present)
        return is_present

    def add_minikube_to_hosts(self):
        self.get_minikube_ip()

        name = "Add minikube.local to /etc/hosts"
        cmd = "bash -c \"echo $'{0}\tminikube.local registry.minikube.local elasticsearch.minikube.local kibana.minikube.local kafka.minikube.local rest.kafka.minikube.local grafana.minikube.local flink.minikube.local neo4j.minikube.local' >> /etc/hosts\"".format(self.settings.master_ip)
        Static.msg(name, '.')
        Cmd.local_sudo_prompt_run(name, cmd)

    def update_minikube_in_hosts(self):
        self.get_minikube_ip()

        name = "Update minikube.local to /etc/hosts"
        cmd = "sed -i -e $'s/.*minikube.*/{0}\tminikube.local registry.minikube.local elasticsearch.minikube.local kibana.minikube.local  kafka.minikube.local rest.kafka.minikube.local grafana.minikube.local flink.minikube.local neo4j.minikube.local/' /etc/hosts".format(self.settings.master_ip)
        Static.msg(name, '.')
        Cmd.local_sudo_prompt_run(name, cmd)

    def get_minikube_ip(self):
        name = "Get minikube ip"
        cmd = "minikube ip"
        self.settings.master_ip = Cmd.local_run_get_out(name, cmd)
        return self.settings.master_ip
