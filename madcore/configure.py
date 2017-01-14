from __future__ import print_function

import getpass
import logging
import os
import subprocess
import sys

import boto3
from questionnaire import Questionnaire

import const
from base import CloudFormationBase
from configs import config
from libs.aws import AwsLambda, AwsConfig
from libs.bitbucket import Bitbucket


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

    def get_ec2_key_pairs(self, region_name):
        client = self.get_aws_client('ec2', region_name=region_name)

        return [key['KeyName'] for key in client.describe_key_pairs()['KeyPairs']]

    def run_cmd(self, cmd, debug=True, cwd=None):
        if debug:
            self.log.info("Running cmd: %s", cmd)

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, cwd=cwd)
        out, err = process.communicate()

        if err:
            self.log.error("ERROR: %s", err)
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

    def configure_ssh_public_key(self):
        """Ask user to upload an ssh key to ec2"""

        self.log.info("Create AWS KeyPair from local ssh key")
        ssh_path = os.path.join(os.path.expanduser("~"), '.ssh')

        if not os.path.exists(ssh_path):
            self.log.error("No ssh path found at: '%s'", ssh_path)
            self.log.info("Can't continue configuration. EXIT.")
            sys.exit(1)

        default_ssh_key_path = os.path.join(ssh_path, 'id_rsa.pub')
        if not os.path.exists(default_ssh_key_path):
            self.log.error("No ssh key found at: '%s'", default_ssh_key_path)
            self.log.info("Can't continue configuration. EXIT.")
            sys.exit(1)
        else:
            while True:
                selected_file = self.raw_prompt('ssh_pub_file',
                                                'Input ssh public key path to use [%s]: ' % default_ssh_key_path)
                if not selected_file['ssh_pub_file'].strip():
                    self.log.debug("Using default key: '%s'", default_ssh_key_path)
                    selected_file['ssh_pub_file'] = default_ssh_key_path
                    break
                else:
                    ssh_file = os.path.expanduser(selected_file['ssh_pub_file'])
                    if not os.path.exists(ssh_file):
                        self.log.error("File does not exists: '%s'", ssh_file)
                        self.log.info("Try again.")
                    else:
                        self.log.debug("OK, using ssh key from: '%s'", ssh_file)
                        break
            while True:
                # TODO@geo validate key to some format
                selected_key_name = self.raw_prompt('key_name', 'Input key name: ')
                key_name = selected_key_name['key_name']
                if not key_name.strip():
                    self.log.error("Invalid key name, try again.")
                else:
                    self.log.info("Key name set to: %s", key_name)
                    break

        ssh_file = os.path.expanduser(selected_file['ssh_pub_file'])

        with open(ssh_file, 'rb') as f:
            ec2_cli = self.get_aws_client('ec2')
            try:
                ec2_cli.import_key_pair(KeyName=key_name, PublicKeyMaterial=f.read())
                return {'key_name': key_name, 'ssh_pub_file': ssh_file}
            except Exception as e:
                self.log.error("Error importing key pair.")
                self.log.error(e)
                self.log.info("Can't continue configuration. EXIT.")
                sys.exit(1)

    def configure_ssh_private_key(self):
        """Ask user for the private key that will be used to ssh"""

        self.log.info("Map local private key file")

        while True:
            selected_file = self.raw_prompt('ssh_priv_file',
                                            'Input ssh private key path to use: ')
            ssh_file = os.path.expanduser(selected_file['ssh_priv_file'])
            if not os.path.exists(ssh_file):
                self.log.error("Key does not exists at: '%s', try again.", ssh_file)
            else:
                self.log.debug("OK, using ssh private key from: '%s'", ssh_file)
                break

        return selected_file

    def configure_aws(self):
        self.log.info("Start aws configuration")
        s = boto3.Session()
        credentials = s.get_credentials()

        if credentials is not None:
            self.log.info("AWS credentials are configured.")
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

        if not aws_data.get('region_name', None):
            selected_region = self.single_prompt('region_name', options=aws_config.get_regions(),
                                                 prompt='Select AWS Region')
            aws_data.update(selected_region)
            # push changes to config so that other components know the region
            config.set_aws_data(aws_data)

        # get instance data from the core and fill the data if needed
        core_instance = self.get_core_instance_data()

        if core_instance.get('KeyName', None):
            self.log.info("Using KeyName: '%s' form the already created instance.", core_instance['KeyName'])
            aws_data['key_name'] = core_instance['KeyName']
        elif not aws_data.get('key_name', None):
            keys_name = self.get_ec2_key_pairs(aws_data['region_name'])

            if keys_name:
                selected_key_name = self.single_prompt('key_name', options=keys_name, prompt='Select AWS KeyPair')
            else:
                self.log.warn("No keys available for region: '{region_name}' in AWS.".format(**aws_data))
                selected_key_name = self.configure_ssh_public_key()

            selected_key_name.update(self.configure_ssh_private_key())

            aws_data.update(selected_key_name)

        if core_instance.get('InstanceType', None):
            self.log.info("Using InstanceType: '%s' form the already created instance.", core_instance['InstanceType'])
            aws_data['instance_type'] = core_instance['InstanceType']
        elif not aws_data.get('instance_type', None):
            selected_instance_type = self.single_prompt('instance_type', options=const.ALLOWED_INSTANCE_TYPES,
                                                        prompt='Select AWS InstanceType')
            aws_data.update(selected_instance_type)

        config.set_aws_data(aws_data)

        self.log.info("End aws configuration.")

    def user_login(self, aws_lambda, user_data):
        self.log.info("Login user(automatically)")
        login_response = aws_lambda.auth_login(user_data['email'], user_data['password'])

        logged_in = login_response.get('login', False)
        if logged_in:
            self.log.info("User successfully logged in.")
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
            self.log.error("User could not login.")

        return logged_in

    def configure_user_registration(self):
        self.log.info("Start user registration.")

        aws_lambda = AwsLambda()

        if not config.is_user_created:
            bitbucket_auth = self.raw_prompt('username', 'Input bitbucket username:')
            bitbucket_auth['password'] = getpass.getpass('Input bitbucket password: ')

            self.log.debug("Connect to bitbucket and get information...")

            bitbucket = Bitbucket(bitbucket_auth['username'], bitbucket_auth['password'])

            try:
                bitbucket.auth.check_auth()
            except Exception:
                self.log.error("Invalid bitbucket auth.")
                self.exit()

            # get bitbucket user email which will be used to register user to madcore
            user_email = bitbucket.user.get_primary_email()

            self.log.info("Check if user already exists.")
            user_password = getpass.getpass('Input madcore password: ')

            user_data = {
                'email': user_email,
                'password': user_password,
                'created': False,
                'verified': False,
                'registration': False,
                'dns_delegation': False,
            }
            # set user data here so that we have the info in login
            config.set_user_data(user_data)

            # check if user already exists on madcore
            if self.user_login(aws_lambda, user_data):
                self.log.info("User '%s' exists.", user_email)
            else:
                self.log.info("User does not exists, create: '%s'", user_email)

                teams = bitbucket.teams.get_teams_username()

                selected_team = self.single_prompt('team', options=teams, prompt='Select bitbucket team')
                selected_domain = self.single_prompt('domain', options=self.get_allowed_domains(),
                                                     prompt='Select madcore domain')

                user_sub_domain = '{team}.{domain}'.format(team=selected_team['team'], domain=selected_domain['domain'])

                self.log.info("The following domain will be configured: '%s'" % user_sub_domain)

                user_create_response = aws_lambda.create_user(user_email, user_password, user_sub_domain)

                if user_create_response['created']:
                    self.log.info("User successfully created.")

                    user_data.update({
                        'domain': selected_domain['domain'],
                        'sub_domain': selected_team['team'],
                        'created': True
                    })
                    # at this point we save data into config because we know that user already created on madcore part
                    config.set_user_data(user_data)

                    verify_code = self.raw_prompt('verify_code', 'Input verification code(from email): ')

                    self.log.debug("Verify user code.")
                    verify_response = aws_lambda.verify_user(user_email, verify_code['verify_code'])

                    if verify_response['verified']:
                        self.log.info("User successfully verified.")
                        config.set_user_data({'verified': True})
                    else:
                        self.log.error("User was not verified.")
                        self.log.error("verify_response %s", verify_response)
                        self.exit()
                else:
                    self.log.error("User was not created.")
        else:
            user_data = config.get_user_data()

        if not config.is_logged_in or not config.is_user_created:
            user_logged_in = self.user_login(aws_lambda, user_data)

            if not user_logged_in:
                self.exit()
        else:
            self.log.debug("User already created and logged in.")

        self.log.info("End user registration.")

    def configure_repos(self):
        self.log.info("Start cloning all required repos.")

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

        self.log.info("End cloning all required repos.")

        return columns, data

    def start_configuration(self):
        self.log_piglet("Configuration")

        if not os.path.exists(self.config_path):
            raw_input(
                "Madcore will now create ~/.madcore folder to store configuration settings. Press enter to begin configuration ")

        self.log_piglet("User Registration")
        self.configure_user_registration()

        self.log_piglet("AWS Configuration")
        self.configure_aws()

        self.log_piglet("Clone repos")
        columns, data = self.configure_repos()

        return columns, data
