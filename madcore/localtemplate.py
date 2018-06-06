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

from jinja2 import Environment, PackageLoader, FileSystemLoader
import os
from prettytable import PrettyTable
import static


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


class LocalTemplate(object):

    settings = None

    def __init__(self, in_settings):
        self.settings = in_settings

    def generate_template(self, name):

        #env = Environment(loader=PackageLoader('localtemplate', 'templates'))
        env = Environment(loader=FileSystemLoader(self.settings.folder_app_templates))
        template = env.get_template(name)
        rendered = template.render(settings=self.settings)

        template_save_path = "{0}/{1}".format(self.settings.folder_user_populated, name)
        with open(template_save_path, "wb") as f:
            f.write(rendered.encode("UTF-8"))
        f.close()

    def generate_template_node(self, file_template, file_populated, ig):
        env = Environment(loader=FileSystemLoader(self.settings.folder_app_templates))
        template = env.get_template(file_template)
        rendered = template.render(ig=ig, settings=self.settings)

        save_path = "{0}/{1}".format(self.settings.folder_user_populated, file_populated)
        with open(save_path, "wb") as f:
            f.write(rendered.encode("UTF-8"))
        f.close()

    def generate_template_element(self, item):
        env = Environment(loader=FileSystemLoader(self.settings.folder_app_templates))
        template = env.get_template(item.template)
        rendered = template.render(component=item, settings=self.settings)

        if self.settings.provision.cloud == "minikube":
            rendered = self.overwrite_nodeselector_for_minikube (rendered)

        template_save_path = "{0}/{1}".format(self.settings.folder_user_populated, item.template)
        with open(template_save_path, "wb") as f:
            f.write(rendered.encode("UTF-8"))
        f.close()

    def overwrite_nodeselector_for_minikube(self, data):
        out = ''
        lines = data.split('\n')
        for line in lines:
            if "kops.k8s.io/instancegroup:" in line:
                number_of_leading_spaces = len(line) - len(line.lstrip())
                line = "{0}kubernetes.io/hostname: minikube".format(' ' * number_of_leading_spaces)
            out += '{0}\n'.format(line)
        return out

