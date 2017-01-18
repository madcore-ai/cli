from __future__ import print_function

import json
import logging
import os
import sys
import time
from collections import OrderedDict

import boto3
import botocore.exceptions
import requests
import requests.exceptions
import urllib3
from cliff.formatters.table import TableFormatter
from jenkins import Jenkins
from jenkins import JenkinsException
from questionnaire import Questionnaire

from madcore import const
from madcore import utils
from madcore.configs import config
from madcore.libs.figlet import figlet


class MadcoreBase(object):
    logger = logging.getLogger(__name__)
    logger_simple = logging.getLogger('no_formatter')
    logger_file_simple = logging.getLogger('file_no_formatter')

    @property
    def config_path(self):
        return utils.project_config_dir()

    @property
    def is_config_file_created(self):
        return os.path.exists(utils.config_file_path())

    def get_cf_template_local(self, template_file):
        with open(os.path.join(self.config_path, 'cloudformation', template_file)) as content_file:
            content = content_file.read()
        return content

    @classmethod
    def get_ipv4(cls):
        http = urllib3.PoolManager()
        response = http.request('GET', 'http://ipv4.icanhazip.com/')
        if response.status is not 200:
            raise RuntimeError('No Internet')
        return response.data.strip()
        # return '8.8.8.8'

    @classmethod
    def list_diff(cls, list1, list2):
        return [x for x in list1 if x not in list2]

    def get_json_from_url(self, url=None):
        try:
            return requests.get(url).json()
        except requests.exceptions.HTTPError as http_error:
            self.logger.error("Error downloading url from: '%s'", url)
            raise http_error

    def get_allowed_domains(self, url=None):
        try:
            url = url or 'https://raw.githubusercontent.com/madcore-ai/plugins/master/domain-index.json'
            return self.get_json_from_url(url)
        except requests.exceptions.HTTPError:
            self.logger.error("Error downloading domain from: '%s'", url)

    def log_figlet(self, msg, *args):
        if args:
            msg %= tuple(args)
        self.logger_simple.info(figlet.renderText(msg))
        self.logger.info(msg)

    def exit(self):
        self.logger.info("EXIT")
        sys.exit(1)

    def wait_until_url_is_up(self, url, log_msg=None, verify=False, max_timeout=600, sleep_time=10):
        elapsed_sec = 0
        while True:
            try:
                response = requests.get(url, verify=verify, timeout=max_timeout)
                response.raise_for_status()
                return True
            except Exception:
                if log_msg:
                    self.logger.info(log_msg)
                elapsed_sec += sleep_time
                if elapsed_sec > max_timeout:
                    break
                time.sleep(sleep_time)

        return False

    @classmethod
    def get_endpoint_url(cls, endpoint):
        return 'https://%s.%s' % (endpoint, config.get_full_domain())


class AwsBase(object):
    def get_aws_client(self, name, **kwargs):
        params = self.get_aws_connection_params.copy()
        params.update(kwargs)
        return boto3.client(name, **params)

    def get_aws_resource(self, name, **kwargs):
        params = self.get_aws_connection_params.copy()
        params.update(kwargs)
        return boto3.resource(name, **params)

    @property
    def get_aws_connection_params(self):
        region_name = config.get_aws_data('region_name')

        params = {}
        if region_name:
            params['region_name'] = region_name

        return params

    def get_hosted_zone_name_servers(self, zone_id):
        client = self.get_aws_client('route53')
        zone = client.get_hosted_zone(Id=zone_id)

        return zone['DelegationSet']['NameServers']

    def describe_instance(self, instance_id):
        ec2_cli = self.get_aws_client('ec2')
        instance_details = ec2_cli.describe_instances(
            InstanceIds=[instance_id]
        )

        try:
            return instance_details['Reservations'][0]['Instances'][0]
        except IndexError:
            return {}

    def is_instance_terminated(self, instance_id):
        instance_details = self.describe_instance(instance_id)

        if not instance_details:
            return True

        instance_status = instance_details['State']['Name']

        if instance_status in ['terminated', 'shutting-down']:
            ec2_cli = self.get_aws_client('ec2')
            ec2_cli.get_waiter('instance_terminated').wait(
                InstanceIds=[instance_id]
            )
            return True

        return False


class CloudFormationBase(MadcoreBase, AwsBase):
    def __init__(self, app, app_args, cmd_name=None):
        # make sure you define parameters here by name and not using *args, **kwargs
        # because inspect.getargspec will give false results in cliff
        super(CloudFormationBase, self).__init__(app, app_args, cmd_name=cmd_name)

        self.formatter = TableFormatter()
        self._session = None
        self._cf_client = None

    def show_table_output(self, column_names, data):
        # TODO#geo a hack to make this work without input parsed args
        # we may consider to change this an extend to properly implement all the formatters
        parsed_args = type(str("Namespace"), (object,), {"print_empty": False, "max_width": 500})
        self.formatter.emit_list(column_names, data, Stdout(), parsed_args)

    @property
    def session(self):
        if self._session is None:
            self._session = boto3.Session(**self.get_aws_connection_params)

        return self._session

    @property
    def cf_client(self):
        if self._cf_client is None:
            self._cf_client = self.session.client('cloudformation')

        return self._cf_client

    @classmethod
    def stack_name(cls, stack_short_name):
        """Given the short stack name, like s3, network, core, output the proper name"""

        return const.STACK_SHORT_NAMES[stack_short_name]

    def get_stack(self, stack_name, debug=True):
        try:
            stack = self.cf_client.describe_stacks(
                StackName=stack_name
            )
            return stack['Stacks'][0]
        except botocore.exceptions.ClientError as cf_error:
            if debug:
                self.logger.error(cf_error)
        except Exception as error:
            if debug:
                self.logger.error(error)

        return None

    def get_stack_by_short_name(self, stack_short_name, **kwargs):
        return self.get_stack(self.stack_name(stack_short_name), **kwargs)

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
                (event['ResourceStatus'] in ['%s_COMPLETE' % event_type, '%s_ROLLBACK_COMPLETE' % event_type,
                                             'ROLLBACK_COMPLETE']):
            return False

        return True

    def show_stack_events_progress(self, stack_name, event_type, wait_seconds=3):
        try:
            response_events = self.cf_client.describe_stack_events(
                StackName=stack_name
            )
        except botocore.exceptions.ClientError as client_error:
            self.logger.error(client_error)
            return

        shown_events = []

        # Kinda a hack to not show old stuff
        for event in response_events['StackEvents']:
            if event['EventId'] not in shown_events:
                shown_events.append(event['EventId'])

        last_event_id = response_events['StackEvents'][0]['EventId']

        # TODO@geo Maybe we should investigate and see if we can create this table using PrettyTable?
        # Display top of updates stream
        self.logger_file_simple.info("{: <45} {: <23} {: <}".format("Resource", "Status", "Details"))

        # Steam updates until we hit a closing case
        while self.maintain_loop(response_events, last_event_id, event_type):
            time.sleep(wait_seconds)
            try:
                response_events = self.cf_client.describe_stack_events(
                    StackName=stack_name,
                )
            except botocore.exceptions.ClientError:
                # we reach a point when we try to describe the stack events but is already deleted
                break

            events = sorted(response_events['StackEvents'], key=lambda x: x['Timestamp'])

            for event in events:
                if event['EventId'] not in shown_events:

                    if 'ResourceStatusReason' not in event:
                        event['ResourceStatusReason'] = ""

                    self.logger_file_simple.info("{: <40} {: <30} {: <}".format(event['ResourceType'],
                                                                                event['ResourceStatus'],
                                                                                event['ResourceStatusReason']))
                    shown_events.append(event['EventId'])

    def show_create_stack_events_progress(self, stack_name, **kwargs):
        self.show_stack_events_progress(stack_name, 'create', **kwargs)

    def show_update_stack_events_progress(self, stack_name, **kwargs):
        self.show_stack_events_progress(stack_name, 'update', **kwargs)

    def show_delete_stack_events_progress(self, stack_name, **kwargs):
        self.show_stack_events_progress(stack_name, 'delete', **kwargs)

    def get_core_public_ip(self):
        dns_stack = self.get_stack(const.STACK_CORE)
        return self.get_output_from_dict(dns_stack['Outputs'], 'MadCorePublicIp')

    def wait_until_domain_is_encrypted(self, timeout=30):
        url = 'https://%s' % config.get_full_domain()
        return self.wait_until_url_is_up(url, verify=True, max_timeout=timeout, sleep_time=5)

    def get_core_instance_data(self):
        core_stack_details = self.get_stack(const.STACK_CORE, debug=False)

        if core_stack_details is not None:
            if core_stack_details['StackStatus'] in ['CREATE_COMPLETE']:
                instance_id = self.get_output_from_dict(core_stack_details['Outputs'], 'MadCoreInstanceId')
                return self.describe_instance(instance_id)

        return {}

    def get_s3_bucket_name(self):
        stack = self.get_stack(const.STACK_S3, debug=False)
        if stack is not None:
            return self.get_output_from_dict(stack['Outputs'], 'S3BucketName')
        return None


class JenkinsBase(CloudFormationBase):
    @property
    def jenkins_endpoint(self):
        return self.get_endpoint_url('jenkins')

    def show_job_console_output(self, jenkins_server, job_name, build_number, sleep_time=1):
        self.logger.info("Get console output for job: '%s'\n", job_name)
        output_lines = []

        # wait until job is is started to get the output
        while True:
            job_info = jenkins_server.get_job_info(job_name, depth=1)

            if job_info['builds'] and job_info['builds'][0]['building']:
                self.logger.debug("Job removed from queue, start processing")
                break
            time.sleep(1)

        while True:
            output = jenkins_server.get_build_console_output(job_name, build_number)
            new_output = output.split(os.linesep)

            output_diff = self.list_diff(new_output, output_lines)

            job_info = jenkins_server.get_job_info(job_name, depth=1)
            if not output_diff and not job_info['builds'][0]['building']:
                break

            output_lines = new_output
            # only display if there are new lines
            if output_diff:
                for line in output_diff:
                    self.logger.info(line.strip())

            time.sleep(sleep_time)

    def create_jenkins_server(self):
        return Jenkins(self.jenkins_endpoint)

    def jenkins_run_job_show_output(self, job_name, parameters=None, sleep_time=1, retry_times=3):
        """We are retrying this method because there may be cases when jenkins gives an error when making API calls"""

        if parameters:
            column_names = ['Name', 'Value']
            data = parameters.items()
            self.logger.info("[%s] Job input parameter.", job_name)
            self.show_table_output(column_names, data)

        retry_time = 0
        while True:
            try:
                jenkins_server = self.create_jenkins_server()
                job_info = jenkins_server.get_job_info(job_name, depth=1)

                build_number = job_info['nextBuildNumber']

                if job_info['builds'] and job_info['builds'][0]['building']:
                    # current job is already building, get it's number
                    build_number = job_info['builds'][0]['number']
                    self.logger.info("[%s] Job already running.", job_name)
                else:
                    # start the job
                    jenkins_server.build_job(job_name, parameters=parameters)
                    self.logger.info("[%s] Build job.", job_name)

                self.show_job_console_output(jenkins_server, job_name, build_number, sleep_time=sleep_time)

                # get the job SUCCESS status
                job_info = jenkins_server.get_job_info(job_name, depth=1)

                return job_info['lastBuild']['result'] in ['SUCCESS']
            except JenkinsException as jenkins_error:
                retry_time += 1
                if retry_time > retry_times:
                    break
                self.logger.error(jenkins_error)
                self.logger.info("Retry: %s", retry_time)

    def wait_until_jenkins_is_up(self, log_msg='Waiting until Jenkins is up...'):
        return self.wait_until_url_is_up(self.jenkins_endpoint, log_msg=log_msg, verify=False, max_timeout=60 * 60)


class PluginsBase(MadcoreBase):
    _plugins = None

    def load_plugin_index(self):
        with open(os.path.join(self.config_path, 'plugins', 'plugins-index.json')) as content_file:
            return json.load(content_file)

    def get_plugins(self):
        if not self._plugins:
            plugins = []
            for product in self.load_plugin_index()['products']:
                if product['type'] == 'plugin':
                    plugins.append(product)
            self._plugins = plugins

        return self._plugins

    def get_plugin_names(self):
        names = []
        for plugin in self.get_plugins():
            # id have the form plugin.madcore.<plugin_name>
            names.append(plugin['id'].rsplit('.', 1)[-1])

        return names

    def get_plugin_by_name(self, plugin_name):
        plugin_id = self.get_plugin_id(plugin_name)

        for plugin in self.get_plugins():
            if plugin['id'] == plugin_id:
                return plugin

    def get_plugin_parameters(self, plugin_name, job_name, load_general_param=True):
        plugin = self.get_plugin_by_name(plugin_name)

        job_params = {}
        for job in plugin['jobs']:
            if job['name'] == job_name:
                job_params = job['parameters']
                break

        if load_general_param:
            # load also the default params of the plugin for all jobs
            job_params.update(plugin.get('parameters', {}))

        return job_params

    def get_plugin_extra_jobs(self, plugin_name):
        plugin = self.get_plugin_by_name(plugin_name)

        exclude_jobs = ['deploy', 'delete', 'update']

        job_names = []
        for job in plugin['jobs']:
            if job['name'] not in exclude_jobs:
                job_names.append(job['name'])

        return job_names

    @classmethod
    def get_plugin_jobs_prefix(cls):
        return 'madcore.plugin'

    @classmethod
    def get_plugin_id(cls, plugin_name):
        return plugin_name

    def get_plugin_job_name(self, plugin_name, job_name):
        return '.'.join((self.get_plugin_jobs_prefix(), plugin_name, job_name))

    def get_plugin_deploy_job_name(self, plugin_name):
        return self.get_plugin_job_name(plugin_name, 'deploy')

    def get_plugin_delete_job_name(self, plugin_name):
        return self.get_plugin_job_name(plugin_name, 'delete')

    def get_plugin_status_job_name(self, plugin_name):
        return self.get_plugin_job_name(plugin_name, 'status')

    @classmethod
    def ask_for_plugin_parameters(cls, plugin_params, parsed_args, to_upper=True):
        confirm_default = parsed_args.confirm_default_params

        # check if parsed_args have input parameters and override the plugin_params
        for arg_param_key, arg_param_val in vars(parsed_args).items():
            if arg_param_key.startswith('_'):
                # remove leading '_' added by parsed args
                plugin_params[arg_param_key[1:]] = arg_param_val

        input_params_selector = Questionnaire()
        input_params = OrderedDict()
        input_params.update(plugin_params)

        for param_key, param_default_value in plugin_params.items():
            prompt = None

            if param_default_value:
                if confirm_default:
                    prompt = "Input [%s] [%s]" % (param_key, param_default_value or '')
            else:
                prompt = "Input [%s]: " % (param_key,)

            if prompt:
                input_params_selector.add_question(param_key, prompter='raw', prompt=prompt)

        input_params.update(input_params_selector.run())

        # add default values if user does not selected one
        for key, value in input_params.items():
            if not value and plugin_params[key]:
                input_params[key] = plugin_params[key]

        if to_upper:
            # Currently all jobs require upper case params, so we make sure we follow this
            input_params = dict([(key.upper(), value) for key, value in input_params.items()])

        return input_params


class Stdout(object):
    logger = logging.getLogger('file_no_formatter')

    def write(self, msg):
        self.logger.info(msg)
