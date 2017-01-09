from __future__ import print_function, unicode_literals

import logging
import os
import time

import boto3
import urllib3
from cliff.command import Command

from base import ShowOne


class CoreFollowme(ShowOne):
    _description = "TODO@geo add doc here"

    log = logging.getLogger(__name__)

    STACK_NAME = 'MADCORE-FollowMe'

    def get_ipv4(self):
        http = urllib3.PoolManager()
        r = http.request('GET', 'http://ipv4.icanhazip.com/')
        if r.status is not 200:
            raise RuntimeError('No Internet')
        return r.data
        # return '8.8.8.8'

    def get_from_dict(self, dic):
        return next(i for i in dic if i['ParameterKey'] == 'FollowMeIpAddress')['ParameterValue']

    def get_stack_followme(self):
        return self.get_stack(self.STACK_NAME)

    def get_template_local(self, template_file):
        with open(os.path.join(self.config_path, 'cloudformation', template_file), 'r') as content_file:
            content = content_file.read()
        return content

    def maintain_loop(self, response, last_event_id):
        events = sorted(response['StackEvents'], key=lambda x: x['Timestamp'], reverse=True)
        event = events[0]

        if (event['EventId'] != last_event_id) and \
                (event['ResourceType'] == 'AWS::CloudFormation::Stack') and \
                ((event['ResourceStatus'] == 'UPDATE_COMPLETE') or (
                            event['ResourceStatus'] == 'UPDATE_ROLLBACK_COMPLETE')):
            return False

        return True

    def show_stack_events_progress(self, client, stack_name, wait_seconds=3):
        response_events = client.describe_stack_events(
            StackName=stack_name
        )

        shown_events = []

        # Kinda a hack to not show old stuff
        for event in response_events['StackEvents']:
            if event['EventId'] not in shown_events:
                shown_events.append(event['EventId'])

        last_event_id = response_events['StackEvents'][0]['EventId']

        # TODO@geo Maybe we should investigate and see if we can create this table using PrettyTable?
        # Print top of updates stream
        print("{: <30} {: <40} {: <}".format("Resource", "Status", "Details"))

        # Steam updates until we hit a closing case
        while self.maintain_loop(response_events, last_event_id):
            time.sleep(wait_seconds)
            response_events = client.describe_stack_events(
                StackName=stack_name,
            )

            events = sorted(response_events['StackEvents'], key=lambda x: x['Timestamp'])

            for event in events:
                if event['EventId'] not in shown_events:

                    if 'ResourceStatusReason' not in event:
                        event['ResourceStatusReason'] = ""

                    print("{: <30} {: <30} {: <}".format(event['ResourceType'], event['ResourceStatus'],
                                                         event['ResourceStatusReason']))
                    shown_events.append(event['EventId'])

    def stack_update(self, ipv4):
        session = boto3.Session()

        client = session.client('cloudformation')

        update_response = client.update_stack(
            StackName=self.STACK_NAME,
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

        self.show_stack_events_progress(client, self.STACK_NAME)

    def take_action(self, parsed_args):
        ipv4 = self.get_ipv4()
        self.log.info('Core Followme: Your public IP detected as: {0}'.format(ipv4))
        stack = self.get_stack_followme()
        previous_parameters = stack['Parameters']
        ipv4_previous = self.get_from_dict(previous_parameters)
        self.log.info('Updating %s Stack...' % self.STACK_NAME)
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
