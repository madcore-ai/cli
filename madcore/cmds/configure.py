from __future__ import print_function, unicode_literals

import logging
import ssl

import botocore.exceptions
from cliff.lister import Lister

from madcore.base import JenkinsBase
from madcore.configs import config
from madcore.configure import MadcoreConfigure
from madcore.const import DOMAIN_REGISTRATION
from madcore.libs.cloudformation import StackCreate


class Configure(JenkinsBase, Lister):
    _description = "Configure madcore"
    logger = logging.getLogger(__name__)

    def is_backup_found(self):
        # TODO@geo maybe we should check if specific files exists in backup?

        s3_client = self.get_aws_client('s3')
        s3_bucket_name = config.get_user_data('s3_bucket_name') or self.get_s3_bucket_name()

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

    def wait_until_madcore_is_up(self):
        self.log_figlet("Wait until madcore is up")
        if self.wait_until_jenkins_is_up(log_msg='Wait until madcore is up...'):
            self.logger.info("Madcore is up, continue.")
        else:
            self.logger.error("Error while waiting for madcore.")
            self.exit()

    def wait_until_all_endpoint_is_up(self, endpoint):
        msg = "Wait until '%s' is up" % endpoint
        endpoint_url = self.get_endpoint_url(endpoint)

        self.log_figlet(msg)
        if self.wait_until_url_is_up(endpoint_url, log_msg=msg, max_timeout=60 * 10, verify=True):
            self.logger.info("[%s] Endpoint is up, continue.", endpoint)
        else:
            self.logger.error("[%s] Error while waiting for endpoint.", endpoint)
            self.exit()

    def wait_until_all_endpoints_are_up(self):
        self.wait_until_all_endpoint_is_up('kubeapi')
        self.wait_until_all_endpoint_is_up('kubedash')
        self.wait_until_all_endpoint_is_up('grafana')
        self.wait_until_all_endpoint_is_up('jenkins')
        # self.wait_until_all_endpoint_is_up('influxdb')

    def take_action(self, parsed_args):
        # TODO#geo this is a hack to skip ssl verification when we do jenkins registration
        ssl._create_default_https_context = ssl._create_unverified_context

        configure = MadcoreConfigure(self.app, self.app_args)
        config_results = configure.take_action(parsed_args)

        self.log_figlet("Cloudformation")
        stack_create = StackCreate(self.app, self.app_args)
        stack_create.take_action(parsed_args)

        s3_bucket_name = config.get_user_data('s3_bucket_name')
        hostname = config.get_full_domain()

        self.wait_until_madcore_is_up()

        self.log_figlet("Registering let's encrypt ssl")
        self.logger.info("[%s] Check if domain is already encrypted...", hostname)
        is_domain_encrypted = self.wait_until_domain_is_encrypted()
        self.logger.info("[%s] Domain certificate found: %s", hostname, is_domain_encrypted)

        if is_domain_encrypted:
            config.set_user_data({"registration": True})
            self.logger.info("[%s] Domain already registered.", hostname)
        else:
            if self.is_backup_found():
                self.log_figlet("Madcore Backup")
                backup_success = self.jenkins_run_job_show_output('madcore.restore',
                                                                  parameters={'S3BucketName': s3_bucket_name})
                if backup_success:
                    self.logger.info("Successful madcore restore.")
                else:
                    self.logger.error("Error while trying to restore madcore.")
                    self.exit()
            else:
                self.logger.info("[%s] Start domain registration.", hostname)

                job_name = 'madcore.registration'
                parameters = DOMAIN_REGISTRATION.copy()
                parameters['Hostname'] = hostname
                parameters['Email'] = config.get_user_data('email')
                parameters['S3BucketName'] = s3_bucket_name

                success = self.jenkins_run_job_show_output(job_name, parameters=parameters)

                if success:
                    self.logger.info("[%s] Successfully run domain registration.", hostname)
                    config.set_user_data({"registration": True})
                else:
                    self.logger.error("[%s] Error while executing domain registration.", hostname)
                    config.set_user_data({"registration": False})
                    self.exit()

        # enable ssl and run the rest of jenkins jobs via ssl
        ssl._create_default_https_context = ssl.create_default_context

        # make sure all endpoints are up before running selftests
        self.wait_until_all_endpoints_are_up()

        self.log_figlet("Madcore selftests")
        self.app.run_subcommand(['selftest'])

        return config_results
