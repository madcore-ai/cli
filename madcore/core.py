from __future__ import print_function, unicode_literals

import logging

from cliff.command import Command
from cliff.show import ShowOne

from base import CloudFormationBase
from stack_names import FOLLOWME_STACK_NAME


class CoreFollowme(CloudFormationBase, ShowOne):
    _description = "TODO@geo add doc here"

    log = logging.getLogger(__name__)

    def stack_update(self, ipv4):
        update_response = self.client.update_stack(
            StackName=FOLLOWME_STACK_NAME,
            TemplateBody=self.get_template_local('sgfm.json'),
            Parameters=[
                {
                    'ParameterKey': 'FollowMeIpAddress',
                    'ParameterValue': ipv4,
                    'UsePreviousValue': False
                },
                {
                    'ParameterKey': 'VpcId',
                    'UsePreviousValue': True
                },
            ])

        self.show_stack_update_events_progress(FOLLOWME_STACK_NAME)

        return update_response

    def take_action(self, parsed_args):
        ipv4 = self.get_ipv4()
        self.log.info('Core Followme: Your public IP detected as: {0}'.format(ipv4))
        stack = self.get_stack(FOLLOWME_STACK_NAME)
        previous_parameters = stack['Parameters']
        ipv4_previous = self.get_param_from_dict(previous_parameters, 'FollowMeIpAddress')
        self.log.info("Updating '%s' Stack..." % FOLLOWME_STACK_NAME)
        self.stack_update(ipv4)

        columns = ('New IPv4',
                   'Stack ID',
                   'Previous IPv4'
                   )
        data = (''.join(ipv4.split()),
                stack['StackId'],
                ipv4_previous
                )
        return columns, data


class Error(Command):
    """Always raises an error"""

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info('causing error')
        raise RuntimeError('this is the expected exception')
