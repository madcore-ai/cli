from __future__ import print_function, unicode_literals

import json
import logging
import os
import sys
import time

import boto3
import botocore.exceptions
import requests
import requests.exceptions
import urllib3
from cliff.formatters.table import TableFormatter
from jenkins import Jenkins
from jenkins import JenkinsException
from jinja2 import Environment
from questionnaire import Questionnaire

from madcore import const
from madcore import utils
from madcore.configs import config
from madcore.libs.figlet import figlet
from madcore.libs.validators import get_validator


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

        self.jinja_env = Environment()

    def jinja_render_string(self, template_str, **kwargs):
        return self.jinja_env.from_string(template_str).render(**kwargs)

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
        else:
            self.logger.debug("[%s] Job does not have input parameters.", job_name)

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


class PluginsBase(JenkinsBase):
    _plugins = None
    _core_params = {}
    PLUGIN_DEFAULT_JOBS = ['deploy', 'delete', 'update']

    @property
    def madcore_plugin_parameters(self):
        """Define root parameters for all plugins. If plugin will define this parameter and the value is null,
        it will automatically fill it.
        """
        if not self._core_params:
            params = {
                "MADCORE_S3_BUCKET": self.get_s3_bucket_name()
            }

            self._core_params = params

        return self._core_params

    def load_plugin_index(self):
        plugin_index_path = os.path.join(self.config_path, 'plugins', 'plugins-index.json')

        # TODO@geo maybe we should render default jinja parameters from template here?
        # and later one params will have filled values. This may be faster then rendering each
        # 'value' field of parameter
        if os.path.exists(plugin_index_path):
            with open(plugin_index_path, 'r') as content_file:
                return json.load(content_file)

        return {}

    def get_plugins(self):
        if not self._plugins:
            plugins = []
            for product in self.load_plugin_index().get('products', []):
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

    @classmethod
    def _get_parameters_name(cls, param_list):
        return [param['name'] for param in param_list]

    @classmethod
    def _get_parameter_definition(cls, param_name, param_list):
        return next(i for i in param_list if i['name'] == param_name)

    def _populate_core_parameters(self, params_list):
        """CHeck if there are any jinja template for parameters value and fill it with core params"""

        for param in params_list:
            if param['value']:
                try:
                    param['value'] = self.jinja_render_string(param['value'], **self.madcore_plugin_parameters)
                except TypeError:
                    pass

        return params_list

    def override_parameters_if_exists(self, params_list_base, param_list_override):
        # Check the parameters that are present in base list and not in
        params_diff = list(
            set(self._get_parameters_name(params_list_base)) - set(self._get_parameters_name(param_list_override)))

        for new_job_param in params_diff:
            # add new parameter at the top of the override list because plugins level params are important
            param_list_override.insert(0, self._get_parameter_definition(new_job_param, params_list_base))

        param_list_override = self._populate_core_parameters(param_list_override)

        return param_list_override

    @classmethod
    def override_parameters_from_dict_if_exists(cls, params_dict_base, param_list_override):
        for job_param in param_list_override:
            if job_param['name'] in params_dict_base:
                job_param['value'] = params_dict_base[job_param['name']]

        return param_list_override

    @classmethod
    def params_to_jenkins_format(cls, params_list):
        # convert parameters to jenkins format. Jus a simple dict with all param names as keys and
        # uppercase
        return dict([(job_param['name'].upper(), job_param['value']) for job_param in params_list])

    def get_plugin_job_parameters(self, plugin_name, job_name, load_validators=True, check_config=True):
        plugin = self.get_plugin_by_name(plugin_name)

        plugin_parameters = plugin.get('parameters', [])
        job_parameters = []

        for job in plugin.get('jobs', []):
            if job['name'] == job_name:
                job_parameters = job.get('parameters', [])
                break

        job_parameters = self.override_parameters_if_exists(plugin_parameters, job_parameters)

        if check_config:
            # load data from config and populate the parameters
            dict_job_params = config.get_plugin_job_params(plugin_name, job_name) or {}
            job_parameters = self.override_parameters_from_dict_if_exists(dict_job_params, job_parameters)

        if load_validators:
            job_parameters = self.load_plugin_job_validators(job_parameters)

        return job_parameters or []

    @classmethod
    def load_plugin_job_validators(cls, job_params):
        # set validators
        for job_param in job_params:
            job_param['validator'] = get_validator(job_param['type'])

        return job_params

    def get_plugin_extra_jobs(self, plugin_name):
        plugin = self.get_plugin_by_name(plugin_name)

        job_names = []
        for job in plugin.get('jobs', []):
            if job['name'] not in self.PLUGIN_DEFAULT_JOBS and not job.get('private', False):
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

    def ask_for_plugin_parameters(self, plugin_name, plugin_job, parsed_args):
        check_config = True

        if parsed_args.reset_params:
            check_config = False

        job_params = self.get_plugin_job_parameters(plugin_name, plugin_job, check_config=check_config)

        parsed_args_dict = vars(parsed_args)

        # get only params that have trailing _, this are marked as used changed params
        job_args_fields = [field for field in parsed_args_dict.keys() if field.startswith('_')]
        job_params_name = self._get_parameters_name(job_params)

        params_diff = list(set(job_args_fields) - set(job_params_name))

        for job_param in job_params:
            param_name = '_%s' % job_param['name']
            if param_name in params_diff:
                job_param['value'] = parsed_args_dict[param_name]

        confirm_default = parsed_args.confirm_default_params

        input_params_selector = Questionnaire()

        for job_param in job_params:
            prompt = None

            if job_param['value']:
                if confirm_default:
                    prompt = "{description}\nInput {type} field {name}={value} ".format(**job_param)
            elif job_param['value'] is None:
                prompt = "{description}\nInput {type} field {name}= ".format(**job_param)

            if prompt:
                input_params_selector.add_question(job_param['name'], prompter=str('raw'), prompt=prompt,
                                                   type=job_param['validator'])

        user_input_params = input_params_selector.run()

        # check user input parameters and change modified ones
        for job_param in job_params:
            if job_param['name'] in user_input_params:
                # user setup here new value for the param
                # TODO@geo What if some param is set but user wants to put empty value?
                # fix this scenario
                user_param = user_input_params[job_param['name']]
                if user_param or isinstance(user_param, bool):
                    job_param['value'] = user_param

        return job_params

    def get_plugin_job_final_params(self, plugin_name, plugin_job, parsed_args):
        """Get the final parameters. Any other logic related to params should be added here
        """

        plugin_params = self.ask_for_plugin_parameters(plugin_name, plugin_job, parsed_args)

        return plugin_params

    @classmethod
    def set_plugin_jobs_params_to_config(cls, plugin_name, plugin_job, plugin_params, parsed_args):

        config_params = dict(((job_param['name'], job_param['value']) for job_param in plugin_params))

        config.set_plugin_job_params(plugin_name, plugin_job, config_params)

    def remove_plugin_jobs_params_from_config(self, plugin_name, parsed_args, plugin_jobs=None):

        if not plugin_jobs:
            plugin_jobs = self.get_plugin_extra_jobs(plugin_name) + self.PLUGIN_DEFAULT_JOBS

        config.delete_plugin_job_params(plugin_name, plugin_jobs)


class Stdout(object):
    logger = logging.getLogger('file_no_formatter')

    def write(self, msg):
        self.logger.info(msg)
