#!/usr/local/bin/python
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

import os
import settings
import argparse
import sys
import execkops
import elements
import provision
import execkubectl
from cmd import Cmd
from static import Static
import pkg_resources


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('ERROR: %s\n' % message)
        self.print_help()
        sys.exit(2)


def get_version():
    try:
        return pkg_resources.get_distribution("madcore")
    except:
        return Cmd.local_run_get_out("get version", "git describe --tags")


def main(args=None):
    description = "Madcore CLI {0} - (c) 2016-2018 Madcore Ltd <humans@madcore.ai>".format(get_version())
    parser = MyParser(prog="./madcore.py", description=description)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-p', '--provision', dest="provision", metavar=('CLUSTERFILE'), help='provision based on <cllusterfile>', action='store')
    group.add_argument('-c', '--clusterfile', dest="clusterfile", metavar=('CLUSTERFILE'), help='set default clusterfile to input <clusterfile>', action='store')
    group.add_argument('--destroy', help='destroy infrastructure', action='store_true')
    group.add_argument('--kops-update', help='kops update', action='store_true')
    group.add_argument('--kops-validate', help='kopds validate', action='store_true')
    group.add_argument('--kubectl-use-context', help='kubectl use context', action='store_true')
    group.add_argument('--mini-hostname', help='set minikube hostname (will sudo)', action='store_true')
    group.add_argument('--get-attr', dest="attr", help='get atribute', action='store')
    group.add_argument('--install-core', help='install core of Madcore', action='store_true')
    group.add_argument('--install-elk', help='install elk', action='store_true')
    group.add_argument('--install-neo4j', help='install neo4j', action='store_true')
    group.add_argument('--install-kafka', help='install kafka', action='store_true')
    args = parser.parse_args()

    if not args.attr:
        print
        print description
        print

    sett = settings.Settings(args)

    if args.provision:
        prov = provision.Provision(sett)
        prov.start()
        exit(0)

    # make sure correct context is set (based on one set in config file)
    # but not for provision (no context then)
    kc = execkubectl.ExecKubectl(sett)
    kc.use_context()
    if args.clusterfile:
        # switch happens in settings
        kc = execkubectl.ExecKubectl(sett)
        kc.use_context()

    elif args.destroy:
        kops = execkops.ExecKops(sett)
        kops.destroy_cluster()

    elif args.kops_update:
        kops = execkops.ExecKops(sett)
        kops.update_settings()

    elif args.kops_validate:
        kops = execkops.ExecKops(sett)
        kops.validate_cluster()

    elif args.install_core:
        el = elements.Elements(sett)
        el.kubectl_install_elements("core")

    elif args.install_elk:
        el = elements.Elements(sett)
        el.kubectl_install_elements("elk")

    elif args.install_neo4j:
        el = elements.Elements(sett)
        el.kubectl_install_elements("neo4j")

    elif args.install_kafka:
        el = elements.Elements(sett)
        el.kubectl_install_elements("kafka")

    elif args.kubectl_use_context:
        kc = execkubectl.ExecKubectl(sett)
        kc.use_context()

    elif args.mini_hostname:
        prov = provision.Provision(sett)
        prov.mini_hostname()

    elif args.attr:

        if args.attr == "domain":
            sys.stdout.write(settings.provision.domain)

    else:
        Static.figletcyber("STATUS")
        kc = execkubectl.ExecKubectl(sett)
        kc.get_pods()
        kc.get_svc()
        kc.get_ing()


if __name__ == "__main__":
    main()

