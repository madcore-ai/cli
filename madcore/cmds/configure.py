from __future__ import print_function, unicode_literals

import logging
import ssl

import botocore.exceptions
from cliff.lister import Lister

from madcore import const
from madcore.base import JenkinsBase
from madcore import configs
from madcore.configs import config
from madcore.configure import MadcoreConfigure
from madcore.const import DOMAIN_REGISTRATION
from madcore.libs import timeouts
from madcore.libs.cloudformation import StackCreate
from madcore.libs.validators import JsonValidator


class Configure(JenkinsBase, Lister):
    _description = "Configure madcore"
    logger = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Configure, self).get_parser(prog_name)

        envs = [const.ENVIRONMENT_PROD, const.ENVIRONMENT_DEV]
        parser.add_argument('env', nargs='?', default=const.ENVIRONMENT_PROD, choices=envs,
                            help="Select the env used to build the project.")
        parser.add_argument('--force', default=False, action='store_true', dest='force',
                            help="Apply for to running the command.")
        parser.add_argument('--upgrade', default=False, action='store_true', dest='upgrade',
                            help="Upgrade repos if there is new changes on remote.")
        parser.add_argument('--update', default={}, dest='update', type=JsonValidator(),
                            help="Upgrade repo with specified values(Input json as {'repo_name': {'branch': "
                                 "'<branch_name>', 'commit': '<commit_id>'}, ...})")

        return parser

    @classmethod
    def enable_ssl(cls):
        ssl._create_default_https_context = ssl.create_default_context

    @classmethod
    def disable_ssl(cls):
        ssl._create_default_https_context = ssl._create_unverified_context

    def is_backup_found(self):
        # TODO@geo maybe we should check if specific files exists in backup?

        s3_client = self.get_aws_client('s3')
        s3_bucket_name = self.get_s3_bucket_name()

        try:
            s3_objects = s3_client.list_objects(
                Bucket=s3_bucket_name,
                Delimiter='/'
            )
            for item in s3_objects.get('CommonPrefixes', []):
                if item['Prefix'] == 'backup/':
                    return True

        except botocore.exceptions.ClientError as s3_error:
            self.logger.error(s3_error)

        return False

    def read_domain_from_backup(self):
        s3_client = self.get_aws_client('s3')
        s3_bucket_name = self.get_s3_bucket_name()

        list_response = s3_client.list_objects(
            Bucket=s3_bucket_name,
            Prefix='backup/certs/openssl.cnf',
            MaxKeys=1
        )

        if list_response.get('Contents', None):
            list_response = list_response['Contents'][0]
            s3_object = s3_client.get_object(
                Bucket=s3_bucket_name,
                IfMatch=list_response['ETag'],
                Key=list_response['Key']
            )

            if s3_object.get('Body', None):
                cnf = configs.OpensslConfig()
                cnf.from_string(s3_object['Body'].read())

                return cnf.get_main_domain_name()

        return None

    def wait_until_madcore_is_up(self):
        self.log_figlet("Wait until madcore is up")
        if self.wait_until_jenkins_is_up(log_msg='Wait until madcore is up...'):
            self.logger.info("Madcore is up, continue.")
        else:
            self.logger.error("Error while waiting for madcore.")
            self.exit()

    def wait_until_endpoint_is_up(self, endpoint):
        msg = "Wait until '%s' is up" % endpoint
        endpoint_url = self.get_endpoint_url(endpoint)

        self.log_figlet(msg)
        endpoint_up = self.wait_until_url_is_up(endpoint_url, log_msg=msg, timeout=timeouts.ENDPOINT_UP_TIMEOUT,
                                                verify=True)
        if endpoint_up:
            self.logger.info("[%s] Endpoint is up: %s.", endpoint, endpoint_url)
            self.log_figlet("%s UP!", endpoint)
        else:
            self.logger.error("[%s] Error while waiting for endpoint.", endpoint)

        return endpoint_up

    def wait_until_all_endpoints_are_up(self):
        endpoints = ['kubeapi', 'kubedash', 'grafana', 'jenkins']

        results = []
        for endpoint in endpoints:
            endpoint_up = self.wait_until_endpoint_is_up(endpoint)
            results.append((endpoint, 'OK' if endpoint_up else 'NOT OK'))

        return results

    def wait_until_all_plugin_endpoints_are_up(self):
        # TODO@geo fix this after we install proper plugins
        endpoints = ['spark', 'zeppelin', 'influxdb']

        results = []
        for endpoint in endpoints:
            results.append((endpoint, 'NOT OK'))

        return results

    def take_action(self, parsed_args):
        config.set_env(parsed_args.env)

        configure = MadcoreConfigure(self.app, self.app_args)
        configure.take_action(parsed_args)

        self.log_figlet("Cloudformation")
        stack_create = StackCreate(self.app, self.app_args)
        stack_create.take_action(parsed_args)

        s3_bucket_name = self.get_s3_bucket_name()
        current_hostname = config.get_full_domain()

        # For now we disable ssl verification
        self.disable_ssl()

        self.wait_until_madcore_is_up()

        self.log_figlet("Registering let's encrypt ssl")
        self.logger.info("[%s] Check if domain is already encrypted...", current_hostname)
        is_domain_encrypted = self.wait_until_domain_is_encrypted()
        self.logger.info("[%s] Domain certificate found: %s", current_hostname, is_domain_encrypted)

        if is_domain_encrypted:
            config.set_user_data({"registration": True})
            self.logger.info("[%s] Domain already registered.", current_hostname)
        else:
            if self.is_backup_found():
                backup_hostname = self.read_domain_from_backup()

                if backup_hostname and backup_hostname != current_hostname:
                    self.logger.error("We have backup for domain: '%s'", backup_hostname)
                    self.logger.error("Current domain is: '%s'", current_hostname)
                    self.exit()

                self.log_figlet("Madcore Backup")
                backup_success = self.jenkins_run_job_show_output('madcore.restore',
                                                                  parameters={'S3BucketName': s3_bucket_name})
                if backup_success:
                    self.logger.info("Successful madcore restore.")
                else:
                    self.logger.error("Error while trying to restore madcore.")
                    self.exit()
            else:
                self.logger.info("[%s] Start domain registration.", current_hostname)

                job_name = 'madcore.registration'
                parameters = DOMAIN_REGISTRATION.copy()
                parameters['Hostname'] = current_hostname
                parameters['Email'] = config.get_user_data('email')
                parameters['S3BucketName'] = s3_bucket_name

                success = self.jenkins_run_job_show_output(job_name, parameters=parameters)

                if success:
                    self.logger.info("[%s] Successfully run domain registration.", current_hostname)
                    config.set_user_data({"registration": True})
                else:
                    self.logger.error("[%s] Error while executing domain registration.", current_hostname)
                    config.set_user_data({"registration": False})
                    self.exit()

        # enable ssl verification and all the checks are done on the encrypted endpoint
        self.enable_ssl()

        # make sure all endpoints are up before running selftests
        endpoints_status = self.wait_until_all_endpoints_are_up()
        endpoints_status += self.wait_until_all_plugin_endpoints_are_up()

        self.log_figlet("Madcore selftests")
        self.app.run_subcommand(['selftest'])

        return ('Endpoint', 'Status'), endpoints_status
