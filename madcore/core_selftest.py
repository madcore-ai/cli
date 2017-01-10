from __future__ import print_function, unicode_literals

from cliff.lister import Lister

from base import CloudFormationBase


class CoreSelfTest(CloudFormationBase, Lister):
    def take_action(self, parsed_args):
        pass
