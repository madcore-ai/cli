from __future__ import print_function

import getpass
import logging
import os
import subprocess
import sys

import boto3
import botocore.exceptions
from cliff.command import Command
from questionnaire import Questionnaire

from madcore import const
from madcore.base import CloudFormationBase
from madcore.configs import config
from madcore.libs.aws import AwsLambda, AwsConfig
from madcore.libs.bitbucket import Bitbucket, AuthError


class MadcoreConfigure(CloudFormationBase, Command):
    logger = logging.getLogger(__name__)

    @classmethod
    def raw_prompt(cls, key, description):
        questionnaire = Questionnaire()
        questionnaire.add_question(key, prompter='raw', prompt=description)
        return questionnaire.run()

    @classmethod
    def single_prompt(cls, key, options=None, prompt=''):
        questionnaire = Questionnaire()
        questionnaire.add_question(key, prompter='single', options=options, prompt=prompt)
        return questionnaire.run()

    def get_ec2_key_pairs(self, region_name):
        client = self.get_aws_client('ec2', region_name=region_name)

        return [key['KeyName'] for key in client.describe_key_pairs()['KeyPairs']]

    def run_cmd(self, cmd, debug=True, cwd=None):
        if debug:
            self.logger.info("Running cmd: %s", cmd)

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, cwd=cwd)
        out, err = process.communicate()

        if err:
            self.logger.error("ERROR: %s", err)
        else:
            if debug:
                self.logger.info('OK')

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

    def configure_ssh_public_key(self):
        """Ask user to upload an ssh key to ec2"""

        self.logger.info("Create AWS KeyPair from local ssh key")
        ssh_path = os.path.join(os.path.expanduser("~"), '.ssh')

        if not os.path.exists(ssh_path):
            self.logger.error("No ssh path found at: '%s'", ssh_path)
            self.logger.info("Can't continue configuration. EXIT.")
            sys.exit(1)

        default_ssh_key_path = os.path.join(ssh_path, 'id_rsa.pub')
        if not os.path.exists(default_ssh_key_path):
            self.logger.error("No ssh key found at: '%s'", default_ssh_key_path)
            self.logger.info("Can't continue configuration. EXIT.")
            sys.exit(1)
        else:
            while True:
                selected_file = self.raw_prompt('ssh_pub_file',
                                                'Input ssh public key path to use [%s]: ' % default_ssh_key_path)
                if not selected_file['ssh_pub_file'].strip():
                    self.logger.debug("Using default key: '%s'", default_ssh_key_path)
                    selected_file['ssh_pub_file'] = default_ssh_key_path
                    break
                else:
                    ssh_pub_file = os.path.expanduser(selected_file['ssh_pub_file'])
                    if not os.path.exists(ssh_pub_file):
                        self.logger.error("File does not exists: '%s'", ssh_pub_file)
                        self.logger.info("Try again.")
                    else:
                        self.logger.debug("OK, using ssh key from: '%s'", ssh_pub_file)
                        break
            while True:
                # TODO@geo validate key to some format
                selected_key_name = self.raw_prompt('key_name', 'Input key name: ')
                key_name = selected_key_name['key_name']
                if not key_name.strip():
                    self.logger.error("Invalid key name, try again.")
                else:
                    self.logger.info("Key name set to: %s", key_name)
                    break

        ssh_pub_file = os.path.expanduser(selected_file['ssh_pub_file'])

        with open(ssh_pub_file, 'rb') as ssh_file:
            ec2_cli = self.get_aws_client('ec2')
            try:
                ec2_cli.import_key_pair(KeyName=key_name, PublicKeyMaterial=ssh_file.read())
                return {'key_name': key_name, 'ssh_pub_file': ssh_pub_file}
            except botocore.exceptions.ClientError as ec2_error:
                self.logger.error("Error importing key pair.")
                self.logger.error(ec2_error)
                self.logger.info("Can't continue configuration. EXIT.")
                sys.exit(1)

    def configure_ssh_private_key(self):
        """Ask user for the private key that will be used to ssh"""

        self.logger.info("Map local private key file")

        default_priv_key_path = '~/.ssh/id_rsa'

        while True:
            selected_file = self.raw_prompt('ssh_priv_file',
                                            'Input ssh private key path to use[%s]: ' % default_priv_key_path)
            ssh_file = os.path.expanduser(selected_file['ssh_priv_file'])
            if not ssh_file:
                ssh_file = os.path.expanduser(default_priv_key_path)
                # we don't need to show this into prompt anymore because does not exists
                default_priv_key_path = ''

            if not os.path.exists(ssh_file):
                self.logger.error("Key does not exists at: '%s', try again.", ssh_file)
            else:
                self.logger.debug("OK, using ssh private key from: '%s'", ssh_file)
                break

        return selected_file

    def configure_aws(self):
        self.logger.info("Start aws configuration")
        session = boto3.Session()
        credentials = session.get_credentials()

        if credentials is not None:
            self.logger.info("AWS credentials are configured.")
        else:
            aws_cmd = self.run_cmd('which aws', debug=False)
            if not aws_cmd:
                self.logger.error("You need to install aws cli!")
                sys.exit(1)
            else:
                self.logger.warn("You need to configure aws!")
                os.system('aws configure')

        aws_config = AwsConfig()
        aws_data = config.get_aws_data()

        if not aws_data.get('region_name', None):
            selected_region = self.single_prompt('region_name', options=aws_config.get_regions(),
                                                 prompt='Select AWS Region')
            aws_data.update(selected_region)
            # push changes to config so that other components know the region
            config.set_aws_data(aws_data)

        # get instance data from the core and fill the data if needed
        core_instance = self.get_core_instance_data()

        if core_instance.get('KeyName', None):
            self.logger.info("Using KeyName: '%s' form the already created instance.", core_instance['KeyName'])
            aws_data['key_name'] = core_instance['KeyName']
        elif not aws_data.get('key_name', None):
            keys_name = self.get_ec2_key_pairs(aws_data['region_name'])

            if keys_name:
                selected_key_name = self.single_prompt('key_name', options=keys_name, prompt='Select AWS KeyPair')
            else:
                self.logger.warn("No keys available for region: '{%s}' in AWS.", aws_data['region_name'])
                selected_key_name = self.configure_ssh_public_key()

            selected_key_name.update(self.configure_ssh_private_key())

            aws_data.update(selected_key_name)

        if core_instance.get('InstanceType', None):
            self.logger.info("Using InstanceType: '%s' form the already created instance.",
                             core_instance['InstanceType'])
            aws_data['instance_type'] = core_instance['InstanceType']
        elif not aws_data.get('instance_type', None):
            selected_instance_type = self.single_prompt('instance_type', options=const.ALLOWED_INSTANCE_TYPES,
                                                        prompt='Select AWS InstanceType')
            aws_data.update(selected_instance_type)

        config.set_aws_data(aws_data)

        self.logger.info("End aws configuration.")

    def user_login(self, aws_lambda, user_data):
        self.logger.info("Login user(automatically)")
        login_response = aws_lambda.auth_login(user_data['email'], user_data['password'])

        logged_in = login_response.get('login', False)
        if logged_in:
            self.logger.info("User successfully logged in.")
            config.set_login_data(login_response)
            # TODO@geo fix this
            # in case that user exists we need a way to check it,
            # at the moment I login and if success I mark user as created, verified
            # get domain from login
            sub_domain, domain = login_response['domain'].split('.', 1)
            user_data.update({'created': True, 'verified': True, 'sub_domain': sub_domain,
                              'domain': domain})
            config.set_user_data(user_data)
        else:
            self.logger.error("User could not login.")

        return logged_in

    def configure_user_registration(self):
        self.logger.info("Start user registration.")

        aws_lambda = AwsLambda()

        if not config.is_user_created:
            bitbucket_auth = self.raw_prompt('username', 'Input bitbucket username:')
            bitbucket_auth['password'] = getpass.getpass('Input bitbucket password: ')

            self.logger.debug("Connect to bitbucket and get information...")

            bitbucket = Bitbucket(bitbucket_auth['username'], bitbucket_auth['password'])

            try:
                bitbucket.auth.check_auth()
            except AuthError:
                self.logger.error("Invalid bitbucket auth.")
                self.exit()

            # get bitbucket user email which will be used to register user to madcore
            user_email = bitbucket.user.get_primary_email()

            self.logger.info("Check if user already exists.")
            user_password = getpass.getpass('Input madcore password: ')

            user_data = {
                'email': user_email,
                'password': user_password,
                'created': False,
                'verified': False,
                'registration': False,
                'dns_delegation': False,
                'config_deleted': True
            }
            # set user data here so that we have the info in login
            config.set_user_data(user_data)

            # check if user already exists on madcore
            if self.user_login(aws_lambda, user_data):
                self.logger.info("User '%s' exists.", user_email)
            else:
                self.logger.info("User does not exists, create: '%s'", user_email)

                teams = bitbucket.teams.get_teams_username()

                selected_team = self.single_prompt('team', options=teams, prompt='Select bitbucket team')
                selected_domain = self.single_prompt('domain', options=self.get_allowed_domains(),
                                                     prompt='Select madcore domain')

                user_sub_domain = '{team}.{domain}'.format(team=selected_team['team'], domain=selected_domain['domain'])

                self.logger.info("The following domain will be configured: '%s'", user_sub_domain)

                user_create_response = aws_lambda.create_user(user_email, user_password, user_sub_domain)

                if user_create_response['created']:
                    self.logger.info("User successfully created.")

                    user_data.update({
                        'domain': selected_domain['domain'],
                        'sub_domain': selected_team['team'],
                        'created': True
                    })
                    # at this point we save data into config because we know that user already created on madcore part
                    config.set_user_data(user_data)

                    verify_code = self.raw_prompt('verify_code', 'Input verification code(from email): ')

                    self.logger.debug("Verify user code.")
                    verify_response = aws_lambda.verify_user(user_email, verify_code['verify_code'])

                    if verify_response['verified']:
                        self.logger.info("User successfully verified.")
                        config.set_user_data({'verified': True})
                    else:
                        self.logger.error("User was not verified.")
                        self.logger.error("verify_response %s", verify_response)
                        self.exit()
                else:
                    self.logger.error("User was not created.")
        else:
            user_data = config.get_user_data()

        if not config.is_logged_in or not config.is_user_created:
            user_logged_in = self.user_login(aws_lambda, user_data)

            if not user_logged_in:
                self.exit()
        else:
            self.logger.debug("User already created and logged in.")

        self.logger.info("End user registration.")

    def configure_repos(self):
        self.logger.info("Start cloning all required repos.")

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

        self.logger.info("End cloning all required repos.")

        return columns, data

    def take_action(self, parsed_args):
        self.log_figlet("Configuration")

        if not os.path.exists(self.config_path):
            inp = "Madcore will now create ~/.madcore folder to store configuration settings. " \
                  "Press enter to begin configuration "
            raw_input(inp)

        self.log_figlet("User Registration")
        self.configure_user_registration()

        self.log_figlet("AWS Configuration")
        self.configure_aws()

        self.log_figlet("Clone repos")
        columns, data = self.configure_repos()

        return columns, data
