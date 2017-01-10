from __future__ import print_function, unicode_literals

import os
import time

import boto3
import urllib3
from botocore.exceptions import ClientError

import stack_names


class MadcoreBase(object):
    @property
    def config_path(self):
        cfg_path = os.path.join(os.path.expanduser("~"), '.madcore')

        return cfg_path

    def get_template_local(self, template_file):
        with open(os.path.join(self.config_path, 'cloudformation', template_file)) as content_file:
            content = content_file.read()
        return content

    @classmethod
    def get_ipv4(cls):
        http = urllib3.PoolManager()
        r = http.request('GET', 'http://ipv4.icanhazip.com/')
        if r.status is not 200:
            raise RuntimeError('No Internet')
        return r.data.strip()
        # return '8.8.8.8'


class CloudFormationBase(MadcoreBase):
    def __init__(self, *args, **kwargs):
        super(CloudFormationBase, self).__init__(*args, **kwargs)
        self.session = boto3.Session()
        self.client = self.session.client('cloudformation')

    @classmethod
    def stack_name(cls, stack_short_name):
        """Given the short stack name, like s3, network, core, output the proper name"""

        return stack_names.STACK_SHORT_NAMES[stack_short_name]

    def get_stack(self, stack_name):
        try:
            r = self.client.describe_stacks(
                StackName=stack_name
            )
            return r['Stacks'][0]
        except ClientError as e:
            self.log.error(e)
        except Exception as e:
            self.log.error(e)

        return None

    def get_stack_by_short_name(self, stack_short_name):
        return self.get_stack(self.stack_name(stack_short_name))

    @classmethod
    def get_param_from_dict(cls, dic, param):
        return next(i for i in dic if i['ParameterKey'] == param)['ParameterValue']

    @classmethod
    def get_output_from_dict(cls, dic, param):
        return next(i for i in dic if i['OutputKey'] == param)['OutputValue']

    @classmethod
    def maintain_loop(cls, response, last_event_id, event_type):
        events = sorted(response['StackEvents'], key=lambda x: x['Timestamp'], reverse=True)
        event = events[0]
        # this can be one of: update, create
        event_type = event_type.upper()

        if (event['EventId'] != last_event_id) and \
                (event['ResourceType'] == 'AWS::CloudFormation::Stack') and \
                (event['ResourceStatus'] in ['%s_COMPLETE' % event_type, '%s_ROLLBACK_COMPLETE' % event_type]):
            return False

        return True

    def show_stack_events_progress(self, stack_name, event_type, wait_seconds=3):
        try:
            response_events = self.client.describe_stack_events(
                StackName=stack_name
            )
        except ClientError as e:
            self.log.error(e)
            return

        shown_events = []

        # Kinda a hack to not show old stuff
        for event in response_events['StackEvents']:
            if event['EventId'] not in shown_events:
                shown_events.append(event['EventId'])

        last_event_id = response_events['StackEvents'][0]['EventId']

        # TODO@geo Maybe we should investigate and see if we can create this table using PrettyTable?
        # Print top of updates stream
        print("{: <45} {: <23} {: <}".format("Resource", "Status", "Details"))

        # Steam updates until we hit a closing case
        while self.maintain_loop(response_events, last_event_id, event_type):
            time.sleep(wait_seconds)
            response_events = self.client.describe_stack_events(
                StackName=stack_name,
            )

            events = sorted(response_events['StackEvents'], key=lambda x: x['Timestamp'])

            for event in events:
                if event['EventId'] not in shown_events:

                    if 'ResourceStatusReason' not in event:
                        event['ResourceStatusReason'] = ""

                    print("{: <40} {: <30} {: <}".format(event['ResourceType'], event['ResourceStatus'],
                                                         event['ResourceStatusReason']))
                    shown_events.append(event['EventId'])

    def show_stack_create_events_progress(self, stack_name, **kwargs):
        self.show_stack_events_progress(stack_name, 'create', **kwargs)

    def show_stack_update_events_progress(self, stack_name, **kwargs):
        self.show_stack_events_progress(stack_name, 'update', **kwargs)

    def show_stack_delete_events_progress(self, stack_name, **kwargs):
        self.show_stack_events_progress(stack_name, 'delete', **kwargs)
