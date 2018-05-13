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
import cmdkubectl
import time

class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

class Elements(object):
    settings = None
    localtemplate = None
    CmdKubectl = None

    def __init__(self, in_settings):
        self.settings = in_settings
        self.localtemplate = localtemplate.LocalTemplate(self.settings)
        self.CmdKubectl = cmdkubectl.CmdKubectl(self.settings)

    def kubectl_install_elements(self, stage):
        name = "ELEMENTS"
        Static.figletcyber('{0} {1}'.format(name, stage.upper()))

        self.CmdKubectl.get_master_ip()
        self.CmdKubectl.get_ingress_ips()

        for element in self.settings.elements[stage]:
            self.create_stage(element)

    def create_stage(self, stage):
        element_item = Struct(**stage)
        self.localtemplate.generate_template_element(element_item)

        # before add taint
        if hasattr(element_item, "taint"):
            if "before" in element_item.taint:
                if element_item.taint["before"] == 'master-remove-all':
                    self.CmdKubectl.taint_remove_from_master()

        # process component
        self.CmdKubectl.apply(element_item)

        # after add taint
        if hasattr(element_item, "taint"):
            if "after" in element_item.taint:
                if element_item.taint["after"] == 'master-add-noschedule':
                    self.CmdKubectl.wait_until_kube_system_ready()
                    self.CmdKubectl.taint_add_to_master_noschedule()

        time.sleep(3)
        print

