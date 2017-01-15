from __future__ import print_function, unicode_literals

import logging

from cliff.show import ShowOne

from madcore.const import STACK_FOLLOWME
from madcore.libs.cloudformation import StackManagement


class Followme(StackManagement, ShowOne):
    _description = "Update Followme stack with current IP"

    logger = logging.getLogger(__name__)

    def followme_stack_update(self, ipv4):
        parameters = [
            {
                'ParameterKey': 'FollowMeIpAddress',
                'ParameterValue': ipv4,
                'UsePreviousValue': False
            },
            {
                'ParameterKey': 'VpcId',
                'UsePreviousValue': True
            },
        ]

        update_response = self.update_stack('sgfm', parameters)

        return update_response

    def take_action(self, parsed_args):
        stack_details = self.get_stack(STACK_FOLLOWME)

        if stack_details is None:
            self.logger.info("Stack not created yet, run configuration to setup.")
            self.exit()

        ipv4 = self.get_ipv4()
        self.logger.info('Core Followme: Your public IP detected as: %s', ipv4)
        previous_parameters = stack_details['Parameters']
        ipv4_previous = self.get_param_from_dict(previous_parameters, 'FollowMeIpAddress')
        if ipv4 == ipv4_previous:
            self.logger.info("No need to update.")
            self.exit()

        self.logger.info("Updating '%s' Stack...", STACK_FOLLOWME)
        self.followme_stack_update(ipv4)

        columns = (
            'New IPv4',
            'Stack ID',
            'Previous IPv4'
        )
        data = (
            ''.join(ipv4.split()),
            stack_details['StackId'],
            ipv4_previous
        )
        return columns, data
