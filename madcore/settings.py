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

import collections
import yamlordereddictloader
import os
import yaml
import subprocess
#from fabric.api import *
import re
from os.path import expanduser
import errno
import cmdkubectl
import os.path
from static import Static
from cmd import Cmd


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


class Settings(object):

    # full arguments object passed
    args = None

    aws_zone = None
    master_ip = None
    ingress_ips = []

    cluster = None
    provision = None
    elements = None

    #current_context = None
    #data_path = None
    #config = None
    #config_locust = None

    settings = None
    filepath_settings = None
    filepath_clusterfile = None

    folder_user = None
    folder_user_populated = None
    folder_user_clusters = None
    folder_app_templates = None
    folder_app_clusters = None

    def __init__(self, args):

        self.args = args

        self.set_user_folders()
        self.set_app_folders()
        self.load_settings_file()

    def set_zone(self):
        if self.provision.cloud == "aws":
            self.aws_zone = "{0}{1}".format(self.provision.region, self.provision.zone_id)

    def set_clusterfile(self):
        # name is file without extension
        # save name and filename
        # init has to replace internal name

        #is in args
        #    is in app or user space
        #is same as settings
        #pass


        def switch_check(in_passed):

            # check if different
            different = False
            if in_passed != self.settings.clusterfile:
                different = True
            else:
                return False

            if different:
                if os.path.isfile(os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), "clusters/"), in_passed)):
                    return True
                else:
                    Static.msg_bold("Error", "Clusterfile file {0} does not exist. Cannot continue.".format(in_passed))
                raise SystemExit(99)

        filepath_app_settings_clusterfile = os.path.join(self.folder_app_clusters, self.settings.clusterfile)
        filepath_user_settings_clusterfile = os.path.join(self.folder_user_clusters, self.settings.clusterfile)

        args_clusterfile = None
        if self.args.provision:
            args_clusterfile = self.args.provision
        elif self.args.clusterfile:
            args_clusterfile = self.args.clusterfile

        filepath_app_args_clusterfile = None
        filepath_user_args_clusterfile = None
        if args_clusterfile:
            # args present - settings UPDATE will happen
            filepath_app_args_clusterfile = os.path.join(self.folder_app_clusters, args_clusterfile)
            filepath_user_args_clusterfile = os.path.join(self.folder_user_clusters, args_clusterfile)

            # check which one exist
            # put that one in settings
            if os.path.isfile(filepath_app_args_clusterfile):
                self.settings.clusterfile = filepath_app_args_clusterfile
            elif os.path.isfile(filepath_user_args_clusterfile):
                self.settings.clusterfile = filepath_user_args_clusterfile
            else:
                Static.msg_bold("Clusterfile Not Found. Cannot Continue. Run madcore with -c flag", filepath_app_args_clusterfile)
                raise SystemExit(98)

        else:
            # using from settings, check if exists
            if os.path.isfile(self.settings.clusterfile):
                Static.msg("Default clusterfile remains as", self.settings.clusterfile)
            else:
                Static.msg_bold("Clusterfile Not Found. Cannot Continue. Run madcore with -c flag to specify new.", self.settings.clusterfile)
                raise SystemExit(99)





        '''

        # switch if required
        switched = False
        if self.args.provision:
            if switch_check(self.args.provision):
                self.settings.settings = self.args.provision
                switched = True

        elif self.args.clusterfile:
            if switch_check(self.args.clusterfile):
                self.settings.settings = self.args.clusterfile
                switched = True

        if switched:
            self.save_settings_file()
            Static.msg("Default clusterfile set to", self.settings.clusterfile)
        else:
            Static.msg("Default clusterfile remains as", self.settings.clusterfile)
        '''

    def load_clusterfile(self):

        clusterfile_data = None
        if os.path.isfile(self.settings.clusterfile):
            clusterfile_data = yaml.load(open(self.settings.clusterfile), Loader=yamlordereddictloader.Loader)
        else:
            Static.msg_bold("Clusterfile not found", self.settings.clusterfile)

        #if os.path.isfile(clusterfile_config_path):
        #    clusterfile_data = yaml.load(open(self.settings.clusterfile), Loader=yamlordereddictloader.Loader)
        #else:
        #    clusterfile_data = yaml.load(open(clusterfile_app_path), Loader=yamlordereddictloader.Loader)

        clusterfile_struct = Struct(**clusterfile_data)
        self.cluster = Struct(**clusterfile_struct.cluster)
        self.provision = Struct(**clusterfile_struct.provision)
        self.elements = clusterfile_data['elements']


        '''
        Static.msg("Initializing", "Clusterfile")
        clusterfile_src = os.path.join(sett.folder_app_clusters, args.init[0])
        clusterfile_dst = os.path.join(sett.folder_config_clusters, args.init[1])

        if os.path.isfile(clusterfile_dst):
            print "DESTINATION FILE {0} ALREADY EXISTS".format(clusterfile_dst)

        if not os.path.isfile(clusterfile_src):
            print "SOURCE FILE {0} NOT FOUND".format(clusterfile_src)

        Cmd.local_run_get_out("CREATED CLUSTERFILE {0}".format(clusterfile_src),
                              "cp {0} {1}".format(clusterfile_src, clusterfile_dst)
                              )

        new_template_name = args.init[0].split(".")
        Cmd.local_run_get_out("UPDATING TEMPLATE NAME", "cp {0} {1}".format(clusterfile_src, clusterfile_dst))
        #sed -i 's/name:*/name: {0}/g'.format(args.init[1]) clusterfile_dst

        # new file goes to ~/.madcore/templates
        #self.settings.folder_clusters #copy to this folder form existing
        '''

    def initialize_new_clusterfile(self):

        clusterfile_src = os.path.join(self.folder_app_clusters, self.args.init[0])
        clusterfile_dst = os.path.join(self.folder_user_clusters, self.args.init[1])

        if os.path.isfile(clusterfile_dst):
            print "DESTINATION FILE {0} ALREADY EXISTS".format(clusterfile_dst)

        if not os.path.isfile(clusterfile_src):
            print "SOURCE FILE {0} NOT FOUND".format(clusterfile_src)

        Static.msg("Initializing New Clusterfile", clusterfile_dst)

        Cmd.local_run_get_out("INITIATED CLUSTERFILE {0}".format(clusterfile_src),
                              "cp {0} {1}".format(clusterfile_src, clusterfile_dst)
                              )

        self.settings.clusterfile = clusterfile_dst
        self.save_settings_file()


        #new_template_name = args.init[0].split(".")
        #Cmd.local_run_get_out("UPDATING TEMPLATE NAME", "cp {0} {1}".format(clusterfile_src, clusterfile_dst))
        #sed -i 's/name:*/name: {0}/g'.format(args.init[1]) clusterfile_dst

        # new file goes to ~/.madcore/templates
        #self.settings.folder_clusters #copy to this folder form existing

    def set_user_folders(self):
        self.folder_user = os.path.join(expanduser("~"), ".madcore")

        self.folder_user_populated = os.path.join(self.folder_user, "rendered")
        if not os.path.exists(self.folder_user_populated):
            self.mkdir_p(self.folder_user_populated)

        self.folder_user_clusters = os.path.join(self.folder_user, "clusters")
        if not os.path.exists(self.folder_user_clusters):
            self.mkdir_p(self.folder_user_clusters)

    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def set_app_folders(self):
        self.folder_app_templates = os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates/"))
        self.folder_app_clusters = os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), "clusters/"))

    def load_settings_file(self):
        self.filepath_settings = os.path.join(self.folder_user, 'settings.yaml')

        if os.path.isfile(self.filepath_settings):
            settings_raw = yaml.load(open(self.filepath_settings))
            settings_raw_struct = Struct(**settings_raw)
            self.settings = Struct(**settings_raw_struct.settings)
        else:
            new_settings = """settings:
    clusterfile: minikube.yaml
"""

            with open(self.filepath_settings, 'wb') as settings_file:
                settings_file.write(new_settings)
            self.load_settings_file()

    def save_settings_file(self):

        # self.config_locust.selected__stream = 'mystream1'
        # self.config_locust.locustfile = 'test.py'
        # self.config_locust.clients = 1
        # self.config_locust.no_web = True
        # self.config_locust.run_time = '1m'

        settings = dict()
        settings['settings'] = self.settings.__dict__

        with open(self.filepath_settings, 'w') as settings_file:
            settings_file.write(yaml.dump(settings, default_flow_style=False))

    def get_populated_filename(self, name):
        return os.path.join(self.folder_user_populated, name)
