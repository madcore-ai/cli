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


class CmdKubectl(object):
    settings = None
    localtemplate = None

    def __init__(self, in_settings):
        self.settings = in_settings
        self.localtemplate = localtemplate.LocalTemplate(self.settings)

    def apply(self, component_item):

        cmd = "kubectl apply -f {0}/{1}".format(
            self.settings.folder_user_populated,
            component_item.template
        )
        Static.msg("Adding Component", component_item.name)
        Cmd.local_run_long(component_item.name, cmd)

    def use_context(self):
        name = "Kubectl Use Context"
        cmd = None
        context = None
        if self.settings.provision.cloud != "minikube":
            cmd = "kubectl config use-context {0}".format(
                self.settings.provision.domain
            )
            context = self.settings.provision.domain
        else:
            cmd = "kubectl config use-context minikube"
            context = "minikube"
        Static.msg(name, context)
        Cmd.local_run_long(name, cmd)
        print

    def get_context(self):
        name = "kubectl config current-context"
        cmd = "kubectl config current-context"
        self.settings.current_context = Cmd.local_run_get_out(name, cmd)
        Static.msg(name,  self.settings.current_context)
        return self.settings.current_context

    def get_master_ip(self):
        name = "Get Master IP"
        if self.get_context() == "minikube":
            cmd = "minikube ip"
            self.settings.master_ip = Cmd.local_run_get_out(name, cmd)
        else:
            cmd = "kubectl get nodes | grep master | sed 's/ .*//'"
            master_node = Cmd.local_run_get_out(name, cmd)
            ip_list = master_node.split('-') # highly dependant on hostname not being changed from amazon default. find better way fast (example: 'ip-172-32-56-155.ec2.internal')
            self.settings.master_ip = '{0}.{1}.{2}.{3}'.format(
                ip_list[1],
                ip_list[2],
                ip_list[3],
                ip_list[4].split('.')[0],
            )

        Static.msg(name, self.settings.master_ip)
        return self.settings.master_ip

    def get_ingress_ips(self):
        name = "Get Ingress IPs"
        if self.get_context() == "minikube":
            cmd = "minikube ip"
            self.settings.ingress_ips.append(self.settings.master_ip)
        else:
            self.settings.ingress_ips = self.get_ig_ips(self.settings.cluster.ingress_instance_group)

        Static.msg(name, self.settings.ingress_ips)
        return self.settings.ingress_ips

    def get_ig_ips(self, ig):
        task = "Get Instancegroup IPS"
        cmd = 'kubectl get nodes -o wide --show-labels | grep "instancegroup={0}" | cut -d" " -f1'.format(ig)
        #        print cmd
        result = Cmd.local_run_get_out_raw(task, cmd)
        outlist = []
        for line in result.split("\n"):
            if line:
                line = line.split('-') # highly dependant on hostname not being changed from amazon default. find better way fast (example: 'ip-172-32-56-155.ec2.internal')
                outlist.append('{0}.{1}.{2}.{3}'.format(
                    line[1],
                    line[2],
                    line[3],
                    line[4].split('.')[0]
                ))

        #       print outlist
        return outlist

    def get_master_node(self):
        name = "Get Master Node"
        cmd = "kubectl get nodes | grep master | sed 's/ .*//'"
        master_node = Cmd.local_run_get_out(name, cmd)
        Static.msg(name, master_node)
        return master_node

    def get_registry_pod(self):
        name = "Get Registry Pod"
        cmd = "kubectl get pods --namespace kube-system -l k8s-app=kube-registry-upstream -o template --template '{{range .items}}{{.metadata.name}} {{.status.phase}}{{\"\\n\"}}{{end}}'"
        master_node = Cmd.local_run_get_out(name, cmd).split(' ')[0]
        Static.msg(name, master_node)
        return master_node

    def registry_port_forward_enable(self):
        name = "Enable PortForward to Registy"
        cmd = "kubectl port-forward --namespace kube-system {0} 5000:5000 & echo $$! > {1}/port-forward.pid".format(
            self.settings.folder_user_populated,
            self.get_registry_pod()
        )
        master_node = Cmd.local_run_get_out(name, cmd)
        Static.msg(name, master_node)
        Static.msg(">", cmd)
        return master_node

    def registry_port_forward_disable(self):
        name = "Disable PortForward to Registy"

        cmd1 = "kill $(shell cat {0}/port-forward.pid) || true".format(self.settings.folder_user_populated)
        cmd1_out = Cmd.local_run_get_out(name, cmd1)
        cmd2 = "rm -f {0}/port-forward.pid".format(self.settings.folder_user_populated)
        cmd2_out = Cmd.local_run_get_out(name, cmd2)

        Static.msg(name, master_node)
        Static.msg(">", cmd)
        return master_node

    def taint_remove_from_master(self):

        name = "Remove Taint Master"
        master_node = self.get_master_node()
        cmd = "kubectl taint nodes {0} node-role.kubernetes.io/master-".format(
            master_node
        )
        Static.msg(name, master_node)
        try:
            Cmd.local_run_long(name, cmd)
        except:
            pass

    def taint_add_to_master_noschedule(self):

        name = "Add Taint Master. No Schedule"
        master_node = self.get_master_node()
        cmd = "kubectl taint nodes {0} node-role.kubernetes.io/master=:NoSchedule".format(
            master_node
        )
        Static.msg(name, master_node)
        Cmd.local_run_long(name, cmd)

    def get_nodes(self):
        name = "Get Nodes"
        cmd = "kubectl get nodes --show-labels -o wide"
        Static.msg(name, self.settings.provision.domain)
        Cmd.local_run_long(name, cmd)
        print

    def get_pods(self):
        name = "Get Pods (sorted by nodeName)"
        cmd = 'kubectl get pods --all-namespaces -o wide --sort-by="{.spec.nodeName}"'
        Static.msg(name, self.settings.provision.domain)
        Cmd.local_run_long(name, cmd)
        print

    def get_svc(self):
        name = "Get Services"
        cmd = "kubectl get svc --all-namespaces"
        Static.msg(name, self.settings.provision.domain)
        Cmd.local_run_long(name, cmd)
        print

    def get_ing(self):
        name = "Get Ingress"
        cmd = "kubectl get ing --all-namespaces"
        Static.msg(name, self.settings.provision.domain)
        Cmd.local_run_long(name, cmd)
        print

    def get_all_on_namespace(self, name):
        cmd = "kubectl get pods,svc,ing --namespace={0}".format(name)
        Static.msg("Displaying status of namespace", name)
        Cmd.local_run_long("Get Namespace Details", cmd)

    def wait_until_kube_system_ready(self):
        name = "Wait Until Kube-System Ready"
        cmd = "kubectl get pods -n kube-system -o=yaml | grep 'ready: true'"
        Static.msg(name, "")
        Cmd.local_run_long_until_ready(name, cmd)




