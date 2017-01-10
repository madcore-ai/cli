from __future__ import print_function, unicode_literals

import logging

from cliff.lister import Lister

import const
from base import CloudFormationBase


class StackDelete(CloudFormationBase, Lister):
    log = logging.getLogger(__name__)
    _description = "Delete stacks"

    def delete_stack(self, stack_short_name, show_progress=True):
        stack_name = self.stack_name(stack_short_name)

        response = self.client.delete_stack(
            StackName=stack_name
        )

        if show_progress:
            self.show_stack_delete_events_progress(stack_name)

        return response

    def delete_stack_if_exists(self, stack_short_name):
        stack_deleted = False
        stack_name = self.stack_name(stack_short_name)

        stack_details = self.get_stack(stack_name)

        if stack_details is not None:
            self.log.info("Stack '%s' exists, delete..." % stack_name)
            self.delete_stack(stack_short_name)
            self.log.info("Stack '%s' deleted." % stack_name)
            stack_deleted = True
        else:
            self.log.info("Stack '%s' does not exists, skip." % stack_name)

        return stack_deleted

    def take_action(self, parsed_args):
        # cluster_deleted = self.delete_stack_if_exists('cluster')
        core_deleted = self.delete_stack_if_exists('core')
        sfgm_deleted = self.delete_stack_if_exists('sgfm')
        network_deleted = self.delete_stack_if_exists('network')
        dns_deleted = self.delete_stack_if_exists('dns')
        # for now we do not delete S3 because it may contain critical information like backups and other
        # s3_deleted = self.delete_stack_if_exists('s3')

        return (
            ('StackName', 'Deleted'),
            (
                # (const.STACK_CLUSTER, cluster_deleted),
                (const.STACK_CORE, core_deleted),
                (const.STACK_FOLLOWME, sfgm_deleted),
                (const.STACK_NETWORK, network_deleted),
                (const.STACK_DNS, dns_deleted),
                (const.STACK_S3, False),
            )
        )
