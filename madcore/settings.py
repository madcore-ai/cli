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


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


class Settings(object):

    # full arguments object passed
    args = None
    cluster = None
    provision = None
    aws_zone = None
    folder_config = None
    folder_populated = None
    master_ip = None
    current_context = None
    data_path = None
    config = None
    config_locust = None
    config_path = None
    elements = None

    def __init__(self, args):

        self.args = args

        self.setup_local_folder()
        self.config_path = os.path.join(self.folder_config, 'config.yaml')
        self.get_config()

        self.switch_config_if_new_requested()

        clusterfile_data = yaml.load(open(os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), "clusters/"), self.config.clusterfile)), Loader=yamlordereddictloader.Loader)
        clusterfile_struct = Struct(**clusterfile_data)
        self.cluster = Struct(**clusterfile_struct.cluster)
        self.provision = Struct(**clusterfile_struct.provision)
        self.elements = clusterfile_data['elements']

        if self.provision.cloud == "aws":
            self.aws_zone = "{0}{1}".format(self.provision.region, self.provision.zone_id)

    # switch default clusterfile
    # quite important so double checking
    def switch_config_if_new_requested(self):

        def switch_check(in_passed):

            # check if different
            different = False
            if in_passed != self.config.clusterfile:
                different = True
            else:
                return False

            if different:
                if os.path.isfile(os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), "clusters/"), in_passed)):
                    return True
                else:
                    Static.msg_bold("Error", "Clusterfile file {0} does not exist. Cannot continue.".format(in_passed))
                raise SystemExit(99)

        # switch if required
        switched = False
        if self.args.provision:
            if switch_check(self.args.provision):
                self.config.clusterfile = self.args.provision
                switched = True

        elif self.args.clusterfile:
            if switch_check(self.args.clusterfile):
                self.config.clusterfile = self.args.clusterfile
                switched = True

        if switched:
            self.save_config()
            Static.msg("Default clusterfile set to", self.config.clusterfile)
        else:
            Static.msg("Default clusterfile remains as", self.config.clusterfile)


    def setup_local_folder(self):

        self.folder_config = os.path.join(expanduser("~"), ".madcore")
        self.folder_populated = os.path.join(self.folder_config, "rendered")
        if not os.path.exists(self.folder_populated):
            self.mkdir_p(self.folder_populated)

    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def get_populated_filename(self, name):
        return os.path.join(self.folder_populated, name)

    def get_config(self):
        if os.path.isfile(self.config_path):
            config_data = yaml.load(open(self.config_path))
            config_data_struct = Struct(**config_data)
            self.config = Struct(**config_data_struct.config)
        else:
            new_config = """config:
    clusterfile: minikube.yaml
"""

            with open(self.config_path, 'wb') as config_file:
                config_file.write(new_config)
            self.get_config()

    def save_config(self):

        # self.config_locust.selected__stream = 'mystream1'
        # self.config_locust.locustfile = 'test.py'
        # self.config_locust.clients = 1
        # self.config_locust.no_web = True
        # self.config_locust.run_time = '1m'

        config = dict()
        config['config'] = self.config.__dict__

        with open(self.config_path, 'w') as config_file:
            config_file.write(yaml.dump(config, default_flow_style=False))

