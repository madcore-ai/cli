from __future__ import print_function, unicode_literals

import logging

import boto3
from cliff.lister import Lister

from base import CloudFormationBase


class StackList(CloudFormationBase, Lister):
    _description = "List stacks"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info('STACK LIST')
        cf = boto3.resource('cloudformation', region_name=self.settings['aws']['Region'])
        return (('Name', 'Status', 'Creation Time', 'Last Updated Time'),
                ([(stack.name, stack.stack_status, stack.creation_time, stack.last_updated_time) for stack in
                  cf.stacks.all()])
                )
