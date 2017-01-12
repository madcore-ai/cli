from __future__ import print_function

import getpass
import os
import subprocess
import sys

import boto3
from questionnaire import Questionnaire

import const
import utils
from base import CloudFormationBase
from configs import config
from libs.aws import AwsLambda, AwsConfig
from libs.bitbucket import Bitbucket
from logs import logging


class MadcoreConfigure(CloudFormationBase):
    log = logging.getLogger(__name__)

    @classmethod
    def raw_prompt(cls, key, description):
        q = Questionnaire()
        q.add_question(key, prompter='raw', prompt=description)
        return q.run()

    @classmethod
    def single_prompt(cls, key, options=None, prompt=''):
        q = Questionnaire()
        q.add_question(key, prompter='single', options=options, prompt=prompt)
        return q.run()

    @classmethod
    def get_ec2_key_pairs(cls, region_name):
        client = boto3.client('ec2', region_name=region_name)
        return [key['KeyName'] for key in client.describe_key_pairs()['KeyPairs']]

    def run_cmd(self, cmd, debug=True, cwd=None):
        if debug:
            self.log.info("Running cmd: %s" % cmd)

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, cwd=cwd)
        out, err = process.communicate()

        if err:
            self.log.error("ERROR: %s" % err)
        else:
            if debug:
                self.log.info('OK')

        return out.strip()

    def clone_repo(self, repo_url):
        repo_folder = os.path.basename(repo_url).split('.')[0]

        repo_path = os.path.join(self.config_path, repo_folder)

        if not os.path.exists(repo_path):
            self.run_cmd('git clone %s' % repo_url, cwd=self.config_path)
        else:
            self.run_cmd('git pull origin master', cwd=repo_path)

        repo_version = self.run_cmd('git describe --tags', cwd=repo_path, debug=False)

        return repo_version

    def configure_aws(self):
        s = boto3.Session()
        credentials = s.get_credentials()

        if credentials is not None:
            self.log.info("AWS is configured!")
        else:
            aws_cmd = self.run_cmd('which aws', debug=False)
            if not aws_cmd:
                self.log.error("You need to install aws cli!")
                sys.exit(1)
            else:
                self.log.warn("You need to configure aws!")
                os.system('aws configure')

        aws_config = AwsConfig()
        aws_data = config.get_aws_data()

        if aws_data.get('region_name', None) is None:
            selected_region = self.single_prompt('region_name', options=aws_config.get_regions(),
                                                 prompt='Select AWS Region')
            aws_data.update(selected_region)

        if aws_data.get('key_name', None) is None:
            keys_name = self.get_ec2_key_pairs(aws_data['region_name'])
            selected_key_name = {'key_name': ''}

            if keys_name:
                selected_key_name = self.single_prompt('key_name', options=keys_name, prompt='Select AWS KeyPair')
                aws_data.update(selected_key_name)
            else:
                self.log.warn("No keys available for region: '{region}'".format(**aws_data))

            aws_data.update(selected_key_name)

        if aws_data.get('instance_type', None) is None:
            selected_instance_type = self.single_prompt('instance_type', options=const.ALLOWED_INSTANCE_TYPES,
                                                        prompt='Select AWS InstanceType')
            aws_data.update(selected_instance_type)

        config.set_aws_data(aws_data)

    def configure_user_registration(self):
        self.log.info("Start user registration")

        aws_lambda = AwsLambda()

        if not config.is_user_created:
            bitbucket_auth = self.raw_prompt('username', 'Input bitbucket username:')
            bitbucket_auth['password'] = getpass.getpass('Input bitbucket password: ')

            bitbucket = Bitbucket(bitbucket_auth['username'], bitbucket_auth['password'])
            teams = bitbucket.teams.get_teams_username()

            selected_domain = self.single_prompt('domain', options=self.get_allowed_domains(),
                                                 prompt='Select bitbucket team')
            selected_team = self.single_prompt('team', options=teams, prompt='Select base domain')

            # get bitbucket user email which will be used to register user
            user_email = bitbucket.user.get_primary_email()

            user_sub_domain = '{team}.{domain}'.format(team=selected_team['team'], domain=selected_domain['domain'])

            self.log.info("Create user: '%s'" % user_email)
            user_password = getpass.getpass('Set madcore password: ')

            user_create_response = aws_lambda.create_user(user_email, user_password, user_sub_domain)

            user_data = {
                'email': user_email,
                'password': user_password,
                'created': False,
                'verified': False,
                'registration': False,
                'dns_delegation': False,
                'domain': selected_domain['domain'],
                'sub_domain': selected_team['team']
            }
            config.set_user_data(user_data)

            if user_create_response['created']:
                self.log.info("User created.")

                config.set_user_data({'created': True})

                verify_code = self.raw_prompt('verify_code', 'Input verify code:')

                self.log.debug("Verify user code")
                verify_response = aws_lambda.verify_user(user_email, verify_code['verify_code'])

                if verify_response['verified']:
                    self.log.info("User verified.")
                    config.set_user_data({'verified': True})
                else:
                    self.log.error("User not verified")
                    self.log.info("verify_response %s" % verify_response)
            else:
                self.log.info("User '%s' already exists." % user_email)
        else:
            user_data = config.get_user_data()

        if not config.is_logged_in or not config.is_user_created:
            self.log.info("Login user(automatically)")
            login_response = aws_lambda.auth_login(user_data['email'], user_data['password'])

            if login_response['login']:
                self.log.info("User successfully logged in.")
                config.set_login_data(login_response)
                # TODO@geo fix this
                # in case that user exists we need a way to check it,
                # at the moment I login and if success user is created
                # get domain from login
                sub_domain, domain = login_response['domain'].split('.', 1)
                config.set_user_data({'created': True, 'verified': True, 'sub_domain': sub_domain,
                                      'domain': domain})
            else:
                self.log.error("Error while logging in.")
                self.log.info('EXIT.')
                sys.exit(1)
        else:
            self.log.debug("Already logged in.")

    def configure_repos(self):
        cf_version = self.clone_repo('https://github.com/madcore-ai/cloudformation.git')
        plugins_version = self.clone_repo('https://github.com/madcore-ai/plugins.git')
        containers_version = self.clone_repo('https://github.com/madcore-ai/containers.git')

        columns = (
            'Project',
            'Version'
        )
        data = (
            ('Cloudformation', cf_version),
            ('Plugins', plugins_version),
            ('Containers', containers_version),
        )

        return columns, data

    def start_configuration(self):
        utils.create_project_config_dir()

        columns, data = self.configure_repos()

        self.configure_aws()
        self.configure_user_registration()

        return columns, data
