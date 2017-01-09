import os
import sys
import logging
from cliff.app import App
from cliff.commandmanager import CommandManager
from cliff.command import Command
from cliff.show import ShowOne
from cliff.lister import Lister
import urllib3
import boto3
from os.path import expanduser
import time



class CoreFollowme(ShowOne):
    """Show a list of files in the current directory.

    The file name and size are printed by default.
    """

    log = logging.getLogger(__name__)

    def get_ipv4(self):
        http = urllib3.PoolManager()
        r = http.request('GET', 'http://ipv4.icanhazip.com/')
        if r.status is not 200:
            raise RuntimeError('No Internet')
        return r.data
        #return '8.8.8.8'

    def get_from_dict(self, dic):
        return next(i for i in dic if i['ParameterKey'] == 'FollowMeIpAddress')['ParameterValue']

    def get_stack_followme(self):
        cf = boto3.client('cloudformation')
        r = cf.describe_stacks(
                StackName='MADCORE-FollowMe'
        )
        return r['Stacks'][0]

    def get_template_local(self,template):
        content = ''
        with open(os.path.join(expanduser("~"),'.madcore/cloudformation/eu-west-1/sgfm.json'), 'r') as content_file:
            content = content_file.read()
        return content

    def maintain_loop(self, response, last_event_id):
        events = sorted(response['StackEvents'], key=lambda x: x['Timestamp'], reverse=True)
        event = events[0]

        if (event['EventId'] != last_event_id) and \
            (event['ResourceType'] == 'AWS::CloudFormation::Stack') and \
                ((event['ResourceStatus'] == 'UPDATE_COMPLETE') or (event['ResourceStatus'] == 'UPDATE_ROLLBACK_COMPLETE')):
            return False

        return True

    def stack_update(self, ipv4):

        session = boto3.Session()

        client = session.client('cloudformation')




#        client = boto3.client('cloudformation')
        r = client.update_stack(
            StackName='MADCORE-FollowMe',
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


 #       responseEvents = client.describe_stack_events(
 #               StackName='MADCORE-FollowMe',
 #       )

#        shown_events = []
#
#        # Kinda a hack to not show old stuff
#        for event in responseEvents['StackEvents']:
#            if event['EventId'] not in shown_events:
#                shown_events.append(event['EventId'])
#
#        last_event_id = r['StackEvents'][0]['EventId']

#        # Print top of updates stream
#        print("{: <30} {: <40} {: <}".format("Resource", "Status", "Details"))

#        # Steam updates until we hit a closing case
#        while self.maintain_loop(responseEvents, last_event_id):
#            time.sleep(3)
#            responseEvents = client.describe_stack_events(
#                StackName='MADCORE-FollowMe',
#            )

#            events = sorted(responseEvents['StackEvents'], key=lambda x: x['Timestamp'])

#            for event in events:
#                if event['EventId'] not in shown_events:

#                    if 'ResourceStatusReason' not in event:
#                        event['ResourceStatusReason'] = ""

#                    print("{: <30} {: <30} {: <}".format(event['ResourceType'], event['ResourceStatus'], event['ResourceStatusReason']))
#                    shown_events.append(event['EventId'])

    def take_action(self, parsed_args):
        ipv4 = self.get_ipv4()
        self.log.info('Core Followme: Your public IP detected as: {0}'.format(ipv4))
        stack = self.get_stack_followme()
        previous_parameters = stack['Parameters']
        ipv4_previous = self.get_from_dict(previous_parameters)
        self.log.info('Updating Madcore-FollowMe Stack...')
        self.stack_update(ipv4)
        columns = ('New IPv4',
            'Stack ID',
            'Previous IPv4'
                   )
        data = (''.join(ipv4.split()),
                stack['StackId'],
                ipv4_previous
                )
        return (columns, data)


class Error(Command):
    "Always raises an error"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info('causing error')
        raise RuntimeError('this is the expected exception')