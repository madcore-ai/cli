from __future__ import print_function, unicode_literals

import logging

from cliff.lister import Lister

from madcore.base import CloudFormationBase


class Stacks(CloudFormationBase, Lister):
    _description = "List stacks"

    logger = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.logger.info('stack list')
        cloudformation = self.get_aws_resource('cloudformation')
        return (
            ('Name', 'Status', 'Creation Time', 'Last Updated Time'),
            ([(stack.name, stack.stack_status, stack.creation_time, stack.last_updated_time) for stack in
              cloudformation.stacks.all()])
        )
