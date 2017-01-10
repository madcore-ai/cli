from __future__ import print_function, unicode_literals

import json
import os
import time

import boto3
import urllib3
from botocore.exceptions import ClientError
from jenkins import Jenkins

import const
import utils


class MadcoreBase(object):
    def __init__(self, *args, **kwargs):
        super(MadcoreBase, self).__init__(*args, **kwargs)

        self.settings = self.get_settings()

    @property
    def config_path(self):
        return utils.config_path()

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

    @classmethod
    def list_diff(cls, l1, l2):
        return [x for x in l1 if x not in l2]

    @classmethod
    def get_settings(cls):
        with open(utils.setting_file_path(), 'r') as f:
            return json.load(f)


class CloudFormationBase(MadcoreBase):
    def __init__(self, *args, **kwargs):
        super(CloudFormationBase, self).__init__(*args, **kwargs)
        self.session = boto3.Session(region_name=self.settings['aws']['Region'])
        self.client = self.session.client('cloudformation')

    @classmethod
    def stack_name(cls, stack_short_name):
        """Given the short stack name, like s3, network, core, output the proper name"""

        return const.STACK_SHORT_NAMES[stack_short_name]

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
            try:
                response_events = self.client.describe_stack_events(
                    StackName=stack_name,
                )
            except ClientError:
                # we reach a point when we try to describe the stack events but is already deleted
                break

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

    def get_dns_domains(self):
        dns_stack = self.get_stack(const.STACK_DNS)
        domain_name = self.get_param_from_dict(dns_stack['Parameters'], 'DomainName')
        sub_domain_name = self.get_param_from_dict(dns_stack['Parameters'], 'SubDomainName')

        return domain_name, sub_domain_name

    def get_core_public_ip(self):
        dns_stack = self.get_stack(const.STACK_CORE)
        return self.get_output_from_dict(dns_stack['Outputs'], 'MadCorePublicIp')


class JenkinsBase(CloudFormationBase, MadcoreBase):
    def __init__(self, *args, **kwargs):
        super(JenkinsBase, self).__init__(*args, **kwargs)

    def show_job_console_output(self, jenkins_server, job_name, build_number, sleep_time=3):
        self.log.info("Get console output for job: '%s'\n" % job_name)
        output_lines = []

        # wait until job is processed
        while True:
            job_info = jenkins_server.get_job_info(job_name)
            if not job_info['inQueue'] and ('_anime' in job_info['color'] or job_info['color'] in ['blue', 'red']):
                self.log.debug("Job removed from queue")
                break
            time.sleep(1)

        while True:
            output = jenkins_server.get_build_console_output(job_name, build_number)
            new_output = output.split(os.linesep)

            output_diff = self.list_diff(new_output, output_lines)

            job_info = jenkins_server.get_job_info(job_name)
            if not output_diff and '_anime' not in job_info['color']:
                break

            output_lines = new_output
            # only print if there are new lines
            if output_diff:
                print(os.linesep.join(output_diff).strip())

            time.sleep(sleep_time)

    def create_jenkins_server(self):
        return Jenkins('https://%s' % self.get_core_public_ip())

    def jenkins_run_job_show_output(self, job_name, parameters=None, sleep_time=3):
        jenkins_server = self.create_jenkins_server()
        job_info = jenkins_server.get_job_info(job_name)
        jenkins_server.build_job(job_name, parameters=parameters)
        self.show_job_console_output(jenkins_server, job_name, job_info['nextBuildNumber'], sleep_time=sleep_time)
