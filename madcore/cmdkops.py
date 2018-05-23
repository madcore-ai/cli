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


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


class CmdKops(object):
    settings = None
    localtemplate = None

    def __init__(self, in_settings):
        self.settings = in_settings
        self.localtemplate = localtemplate.LocalTemplate(self.settings)

        self.file_local_cluster = "kops.1.9.0.cluster.yaml"
        self.file_local_master = "kops.1.9.0.master.yaml"
        self.file_local_nodes = "kops.1.9.0.ig.yaml"

    def get_ig_filename(self, ig):
        return "kops.1.9.0.ig.{0}.yaml".format(ig)

    def create_cluster(self):
        name = "CREATE CLUSTER"
        Static.figletcyber(name)

        cmd = "kops create cluster --zones {0} --vpc {1} --dns-zone={2} --state={3} {4}".format(
            self.settings.aws_zone,
            self.settings.provision.vpc_id,
            self.settings.provision.dnszone_id,
            self.settings.provision.s3_store,
            self.settings.provision.domain
        )
        print cmd
        Static.msg(name, "KOPS: aws")
        Cmd.local_run_long(name, cmd)

        # CREATE INSTANCE_GROUPS ====
    #        for ig in self.settings.provision.instance_groups:
    #            single_ig = Struct(**ig)
    #            if single_ig.name <> "nodes":
    #                self.add_instance_group(single_ig)

    def add_instance_group(self, ig):
        name = "ADD INSTANCE GROUP"
        Static.figletcyber(name)

        cmd = "kops create ig {0} --state={1} {2}".format(
            ig.name,
            self.settings.provision.s3_store,
            self.settings.provision.domain
        )
        Static.msg(name, "KOPS: aws")
        Cmd.local_run_long(name, cmd)

    def destroy_cluster(self):
        name = "DESTROY CLUSTER"
        Static.figletcyber(name)

        cmd = "kops delete cluster --state={0} {1} --yes".format(
            self.settings.provision.s3_store,
            self.settings.provision.domain
        )
        Static.msg(name, "KOPS: aws")
        Cmd.local_run_realtime_continue_on_fail(name, cmd)

    def update_settings(self):
        name = "UPDATE KOPS SETTINGS"
        Static.figletcyber(name)

        # CLUSTER ====
        task = "Get Kops Cluster settings"
        cmd = "kops get cluster -oyaml --state={0} > {1}/remote.{2}".format(
            self.settings.provision.s3_store,
            self.settings.folder_user_populated,
            self.file_local_cluster)
        Static.msg(name, task)
        Cmd.local_run_long(name, cmd)

        task = "Render Cluster Template"
        Static.msg(name, task)
        self.localtemplate.generate_template(self.file_local_cluster)

        task = "Update Kops Clusters settings"
        cmd = "kops replace -f {0}/{1} --state={2}".format(
            self.settings.folder_user_populated,
            self.file_local_cluster,
            self.settings.provision.s3_store
        )
        Static.msg(name, task)
        Cmd.local_run_long(name, cmd)

        # MASTER ====
        task = "Get Kops Master settings"
        cmd = "kops get ig --name={0} master-{1} -oyaml --state={2} > {3}/remote.{4}".format(
            self.settings.provision.domain,
            self.settings.aws_zone,
            self.settings.provision.s3_store,
            self.settings.folder_user_populated,
            self.file_local_master)
        Static.msg(name, task)
        Cmd.local_run_long(name, cmd)

        task = "Render Master Template"
        Static.msg(name, task)
        self.localtemplate.generate_template(self.file_local_master)

        task = "Update Kops Master settings"
        cmd = "kops replace -f {0}/{1} --state={2}".format(
            self.settings.folder_user_populated,
            self.file_local_master,
            self.settings.provision.s3_store
        )
        Static.msg(name, task)
        Cmd.local_run_long(name, cmd)

        # INSTANCE_GROUPS ====
        for ig in self.settings.provision.instance_groups:
            single_ig = Struct(**ig)
            populated_ig_file = self.get_ig_filename(single_ig.name)

            task = "Get Kops Instance Group {0} settings".format(single_ig.name)
            cmd = "kops get ig --name={0} nodes -oyaml --state={1} > {2}/remote.{3}".format(
                self.settings.provision.domain,
                self.settings.provision.s3_store,
                self.settings.folder_user_populated,
                populated_ig_file)
            Static.msg(name, task)
            Cmd.local_run_long(name, cmd)

            task = "Render Instance Group {0} Template".format(single_ig.name)
            Static.msg(name, task)
            self.localtemplate.generate_template_node(self.file_local_nodes, populated_ig_file, single_ig)

            task = "Update Kops Instance Group {0} settings".format(single_ig.name)
            cmd = "kops replace -f {0}/{1} --state={2} --force".format(
                self.settings.folder_user_populated,
                populated_ig_file,
                self.settings.provision.s3_store
            )
            Static.msg(name, task)
            Cmd.local_run_long(name, cmd)

        print

    def add_instance_group(self, name):
        single_ig = Struct(**list(filter(lambda d: d['name'] in [name], self.settings.provision.instance_groups))[0])
        populated_ig_file = self.get_ig_filename(single_ig.name)

        task = "Get Kops Instance Group {0} settings".format(single_ig.name)
        cmd = "kops get ig --name={0} nodes -oyaml --state={1} > {2}/remote.{3}".format(
            self.settings.provision.domain,
            self.settings.provision.s3_store,
            self.settings.folder_user_populated,
            populated_ig_file)
        Static.msg(name, task)
        Cmd.local_run_long(name, cmd)

        task = "Render Instance Group {0} Template".format(single_ig.name)
        Static.msg(name, task)
        self.localtemplate.generate_template_node(self.file_local_nodes, populated_ig_file, single_ig)

        task = "Update Kops Instance Group {0} settings".format(single_ig.name)
        cmd = "kops replace -f {0}/{1} --state={2} --force".format(
            self.settings.folder_user_populated,
            populated_ig_file,
            self.settings.provision.s3_store
        )
        Static.msg(name, task)
        Cmd.local_run_long(name, cmd)

    def provision_cluster(self):
        name = "PROVISION CLUSTER"
        Static.figletcyber(name)

        task = "Provision in Cloud"
        cmd = "kops update cluster {0} --state={1} --yes -v={2} 2>&1".format(
            self.settings.provision.domain,
            self.settings.provision.s3_store,
            self.settings.provision.kops_verbosity
        )
        Static.msg(name, task)
        print cmd
        Cmd.local_run_long(name, cmd)

        self.validate_cluster()

        #task = "Validate Provisioned Cluster"
        #cmd = "kops validate cluster --state={0}".format(
        #    self.settings.provision.s3_store
        #)
        #Cmd.local_run_long_until_success(name, cmd)

    def update_cluster(self):
        name = "UPDATE CLUSTER"
        Static.figletcyber(name)

        task = "Rolling Update CLuster"
        cmd = "kops rolling-update cluster {0} --state={1} --yes -v={2} 2>&1".format(
            self.settings.provision.domain,
            self.settings.provision.s3_store,
            self.settings.provision.kops_verbosity
        )
        Static.msg(name, task)
        print cmd
        Cmd.local_run_long(name, cmd)

        self.validate_cluster()

    def validate_cluster(self):
        name = "VALIDATE CLUSTER"
        task = "Validate Provisioned Cluster"
        cmd = "kops validate cluster --name={0} --state={1} -v={2} 2>&1".format(
            self.settings.provision.domain,
            self.settings.provision.s3_store,
            self.settings.provision.kops_verbosity
        )
        print cmd
        Cmd.local_run_long_until_success(name, cmd)
        Static.msg("Provisioning of Kubernetes Cluster", "VERIFIED")















