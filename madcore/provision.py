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
import cmdkops
import cmdminikube


class Provision(object):
    settings = None
    kops = None
    minikube = None

    def __init__(self, in_settings):
        self.settings = in_settings
        self.kops = cmdkops.CmdKops(self.settings)
        self.minikube = cmdminikube.Minikube(self.settings)

    def start(self):
        Static.figletcyber("PROVISIONING")
        if self.settings.provision.cloud == "aws":
            self.kops.create_cluster()
            self.kops.update_settings()
            self.kops.provision_cluster()
        elif self.settings.provision.cloud == "minikube":
            self.minikube.config_vm_virtualbox()
            self.minikube.start()
            self.minikube.confirm_started()
        else:
            Static.msg_bold("No such provisioner specified in config", self.settings.provision.cloud)
            raise SystemExit(32)

    def mini_hostname(self):
        Static.figletcyber("HOSTNAME")
        if self.minikube.is_minikube_in_hosts():
            # replace, exists
            self.minikube.update_minikube_in_hosts()
        else:
            # append, new
            self.minikube.add_minikube_to_hosts()
        Static.msg("/etc/hosts entry for minikube.local updated to", self.settings.master_ip)

    def destroy(self):
        Static.figletcyber("DESTROY CLUSTER")
        if self.settings.provision.cloud == "aws":
            self.kops.destroy_cluster()
        elif self.settings.provision.cloud == "minikube":
            self.minikube.delete()
        else:
            Static.msg_bold("No such provisioner specified in config", self.settings.provision.cloud)
            raise SystemExit(32)

    def check_alive(self):
        Static.figletcyber("STATUS")
        # not implemented
        if self.settings.provision.cloud == "aws":
            pass
        elif self.settings.provision.cloud == "minikube":
            pass
        else:
            Static.msg_bold("No such provisioner specified in config", self.settings.provision.cloud)
            raise SystemExit(32)