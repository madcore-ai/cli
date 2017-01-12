from __future__ import print_function, unicode_literals

from cliff.show import ShowOne

from madcore.base import CloudFormationBase
from madcore.const import STACK_FOLLOWME
from madcore.logs import logging


class Followme(CloudFormationBase, ShowOne):
    _description = "Update Followme stack with current IP"

    log = logging.getLogger(__name__)

    def stack_update(self, ipv4):
        update_response = self.cf_client.update_stack(
            StackName=STACK_FOLLOWME,
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

        self.show_stack_update_events_progress(STACK_FOLLOWME)

        return update_response

    def take_action(self, parsed_args):
        ipv4 = self.get_ipv4()
        self.log.info('Core Followme: Your public IP detected as: {0}'.format(ipv4))
        stack = self.get_stack(STACK_FOLLOWME)
        previous_parameters = stack['Parameters']
        ipv4_previous = self.get_param_from_dict(previous_parameters, 'FollowMeIpAddress')
        self.log.info("Updating '%s' Stack..." % STACK_FOLLOWME)
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
