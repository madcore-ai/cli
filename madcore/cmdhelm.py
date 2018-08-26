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


class CmdHelm(object):
    settings = None
    localtemplate = None

    def __init__(self, in_settings):
        self.settings = in_settings
        self.localtemplate = localtemplate.LocalTemplate(self.settings)



    def install(self, element):
        name = "INSTALL CHART"

        task = "Populate Chart Values"
        Static.msg(name, task)
        self.localtemplate.generate_template_element(element)


        # name autoassigned, replace to use same name, unsafe in prod, good for testing
        cmd = "helm upgrade --install --debug --namespace {1} --values={2} {0} {3}".format(
            element.release,
            element.name,
            self.localtemplate.path_populated,
            element.chart
        )

        print cmd
        Static.msg(name, "{0}".format(element.chart))
        Cmd.local_run_long(name, cmd)

