from __future__ import print_function, unicode_literals

import logging

from cliff.lister import Lister

from madcore import const
from madcore.configs import config
from madcore.libs.cloudformation import StackManagement


class Destroy(StackManagement, Lister):
    logger = logging.getLogger(__name__)
    _description = "Destroy stacks"

    def take_action(self, parsed_args):
        self.log_figlet("Destroy")
        core_deleted = self.delete_stack_if_exists('core')
        sgfm_deleted = self.delete_stack_if_exists('sgfm')
        network_deleted = self.delete_stack_if_exists('network')
        # dns_deleted = self.delete_stack_if_exists('dns')
        # for now we do not delete S3 because it may contain critical information like backups and other
        # s3_deleted = self.delete_stack_if_exists('s3')

        # keep track that it was deleted
        config.set_user_data({'config_deleted': True})

        return (
            ('StackName', 'Deleted'),
            (
                (const.STACK_CORE, core_deleted),
                (const.STACK_FOLLOWME, sgfm_deleted),
                (const.STACK_NETWORK, network_deleted),
                (const.STACK_DNS, False),
                (const.STACK_S3, False),
            )
        )
