from __future__ import print_function, unicode_literals

import getpass
import logging
import os
import sys

import boto3
import botocore.exceptions
from builtins import input
from cliff.command import Command

from madcore import const
from madcore import utils
from madcore.base import CloudFormationBase
from madcore.configs import config
from madcore.libs.aws import AwsLambda, AwsConfig
from madcore.libs.bitbucket import Bitbucket, AuthError


class MadcoreConfigure(CloudFormationBase, Command):
    logger = logging.getLogger(__name__)

    def get_ec2_key_pairs(self, region_name):
        client = self.get_aws_client('ec2', region_name=region_name)

        return [key['KeyName'] for key in client.describe_key_pairs()['KeyPairs']]

    def clone_repo_latest_version(self, repo_name, branch):
        config_path = os.path.join(self.config_path, '.latest_repos')

        repo_url = os.path.join(const.REPO_MAIN_URL, '%s.git' % repo_name)
        repo_path = os.path.join(config_path, repo_name)

        debug = False
        quiet = '-q'

        if not os.path.exists(repo_path):
            os.makedirs(repo_path)
            self.run_cmd(
                'git clone -b {branch} {repo_url} {quiet}'.format(branch=branch, repo_url=repo_url, quiet=quiet),
                cwd=config_path, debug=debug)
        else:
            self.run_cmd('git checkout {branch} {quiet}'.format(branch=branch, quiet=quiet), cwd=repo_path,
                         debug=debug)
            self.run_cmd('git fetch {quiet}'.format(quiet=quiet), cwd=repo_path, debug=debug)
            self.run_cmd('git reset --hard origin/{branch} {quiet}'.format(branch=branch, quiet=quiet), cwd=repo_path,
                         debug=debug)

        latest_version = self.run_cmd('git describe --tags --always', cwd=repo_path,
                                      debug=debug)
        latest_commit_id = self.run_cmd('git rev-parse HEAD', cwd=repo_path, debug=debug)

        return latest_version, latest_commit_id

    def get_repo_latest_version(self, repo_name, branch):
        pass

    def clone_repo(self, repo_name, parsed_args):
        self.log_figlet("Clone '%s'", repo_name)

        repo_url = os.path.join(const.REPO_MAIN_URL, '%s.git' % repo_name)
        repo_path = os.path.join(self.config_path, repo_name)

        update_repo = parsed_args.update.get(repo_name, {})
        repo_config = config.get_repo_config(repo_name)

        if parsed_args.force:
            # force automatically get the branch from env
            branch = self.env_branch
            commit = 'FETCH_HEAD'
        else:
            branch = repo_config.get('branch', self.env_branch)
            commit = repo_config.get('commit', '') or 'FETCH_HEAD'

            # check if we have input data for update and use that
            branch = update_repo.get('branch', branch)
            commit = update_repo.get('commit', commit)

        remote_version, remote_commit_id = self.clone_repo_latest_version(repo_name, branch)
        upgrade_repo = False

        if not parsed_args.force and not update_repo and parsed_args.upgrade:
            if remote_commit_id != commit:
                self.logger.info("[%s][%s] There is a new updates on remote branch.", repo_name, branch)
                self.logger.info("[%s][%s] Local commit '%s', remote commit '%s'.", repo_name, branch,
                                 commit, remote_commit_id)
                question_text = "[%s] New updates found on branch: '%s'\n" % (repo_name, branch)
                question_text += "[%s] Local commit '%s', remote commit '%s', upgrade?" % (repo_name, commit,
                                                                                           remote_commit_id)

                upgrade_repo = self.ask_question_and_continue_on_yes(question_text, exit_after=False)

        if not os.path.exists(repo_path):
            self.run_cmd('git clone -b %s %s' % (branch, repo_url), cwd=self.config_path, log_prefix=repo_name)
        else:
            self.logger.info("[%s] Repo already exists.", repo_name)

        if not parsed_args.force and not upgrade_repo and repo_config:
            self.logger.info("[%s] Reset repos to version defined in config.", repo_name)
            self.run_git_cmd('git checkout {branch}'.format(branch=branch), repo_name)
            self.run_git_cmd('git fetch', repo_name)
            self.run_git_cmd('git --no-pager log -50 --pretty=oneline', repo_name, log_result=True)
            self.run_git_cmd('git reset --hard {commit}'.format(commit=commit), repo_name, log_result=True)
        else:
            self.logger.info("[%s] Get latest version from branch '%s'.", repo_name, branch)
            self.run_git_cmd('git checkout {branch}'.format(branch=branch), repo_name, log_result=True)
            self.run_git_cmd('git reset --hard origin/{branch}'.format(branch=branch), repo_name, log_result=True)

        self.logger.info("[%s] Last commit on branch '%s'.", repo_name, branch)
        self.run_git_cmd('git --no-pager log -1', repo_name, log_result=True)

        self.logger.info("[%s] Save latest commit in config.", repo_name)
        latest_commit_id = self.run_git_cmd('git rev-parse HEAD', repo_name, debug=False)
        last_version = self.run_git_cmd('git describe --tags --always', repo_name, debug=False)

        repo_data = {
            'branch': branch,
            'commit': latest_commit_id,
            'version': last_version,
            'latest_version': remote_version
        }

        config.set_repo_config(repo_name, repo_data)

    def configure_ssh_public_key(self):
        """Ask user to upload an ssh key to ec2"""

        self.logger.info("Create AWS KeyPair from local ssh key")
        default_ssh_key_path = '~/.ssh/id_rsa.pub'

        while True:
            selected_file = self.raw_prompt('ssh_pub_file',
                                            'Input ssh public key path to use: ',
                                            default=default_ssh_key_path
                                            )

            ssh_pub_file = os.path.expanduser(selected_file['ssh_pub_file'])
            if not os.path.exists(ssh_pub_file):
                self.logger.error("File does not exists: '%s'", selected_file['ssh_pub_file'])
                self.logger.info("Try again.")
            else:
                self.logger.debug("OK, using ssh key from: '%s'", selected_file['ssh_pub_file'])
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
                                            'Input ssh private key path to use ', default=default_priv_key_path)
            ssh_file = os.path.expanduser(selected_file['ssh_priv_file'])

            if not os.path.exists(ssh_file):
                self.logger.error("SSH key does not exists at: '%s', try again.", ssh_file)
                default_priv_key_path = ''
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
                self.logger.warn("No keys available for region: '%s' in AWS.", aws_data['region_name'])
                selected_key_name = self.configure_ssh_public_key()

            aws_data.update(selected_key_name)

        if not aws_data.get('ssh_priv_file', None):
            aws_data.update(self.configure_ssh_private_key())

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

    def verify_user_account(self, aws_lambda, user_email):
        verified = False
        verify_code = self.raw_prompt('verify_code', 'Input verification token(from email): ')

        self.logger.debug("Verify user token.")
        verify_response = aws_lambda.verify_user(user_email, verify_code['verify_code'])

        if verify_response['verified']:
            self.logger.info("User successfully verified.")
            verified = True
            config.set_user_data({'verified': verified})
        else:
            self.logger.error("User was not verified.")

        return verified

    def reset_password(self, aws_lambda, email, new_password=None):
        password_reset = False

        if not new_password:
            new_password = getpass.getpass('Input new madcore password: ')

        self.logger.info("Reset password")
        self.logger.info("Send verification token to '%s'", email)

        lost_password = aws_lambda.lost_password(email)
        if lost_password.get('sent', False):
            verify_token = self.raw_prompt('verify_token', 'Input verification token(from email): ')
            reset_password_response = aws_lambda.reset_password(email, verify_token['verify_token'], new_password)
            if reset_password_response.get('changed', False):
                self.logger.info("Successfully reset password.")
                config.set_user_data({'password': new_password})
                password_reset = True
            else:
                self.logger.error("Error while reset password.")
                self.logger.error(reset_password_response)
        else:
            self.logger.error("Error while sending verification core")

        return password_reset

    def user_login(self, aws_lambda):
        user_exists = False

        self.logger.info("Login user(automatically)")
        user_data = config.get_user_data()

        while True:
            if not user_data:
                break

            email, password = user_data['email'], user_data['password']

            login_response = aws_lambda.auth_login(email, password)

            logged_in = login_response.get('login', False)
            if logged_in:
                user_exists = True
                self.logger.info("User successfully logged in.")
                config.set_login_data(login_response)
                # TODO@geo Check if user is not verified and verify here
                sub_domain, domain = login_response['domain'].split('.', 1)
                user_data.update({
                    'created': user_exists,
                    'verified': True,
                    'sub_domain': sub_domain,
                    'domain': domain,
                    'password': password
                })
                config.set_user_data(user_data)
                break
            else:
                if login_response.get('exist', False):
                    self.logger.debug("Invalid login password")
                    password_option_sel = self.single_prompt('password_option', options=['reset', 'login'],
                                                             prompt='Invalid login password, continue with?')
                    if password_option_sel['password_option'] == 'login':
                        user_data['password'] = getpass.getpass('Input madcore password: ')
                    else:
                        new_password = getpass.getpass('Input new madcore password: ')
                        if self.reset_password(aws_lambda, email, new_password):
                            # continue and it will try to login again with new password, if changed
                            user_data['password'] = new_password
                            continue
                        else:
                            self.exit()
                else:
                    # at this stage we know that uer does not exists and we just exit
                    self.logger.error(login_response['error'])
                    break

        return user_exists

    def start_bitbucket_auth(self):
        self.logger.info("Auth to bitbucket")

        failed_attempts = 0

        while True:
            bitbucket_auth = self.raw_prompt('username', 'Input bitbucket username:')
            bitbucket_auth['password'] = getpass.getpass('Input bitbucket password: ')

            self.logger.debug("Authenticate to bitbucket...")

            bitbucket = Bitbucket(bitbucket_auth['username'], bitbucket_auth['password'])

            try:
                bitbucket.auth.check_auth()
                return bitbucket
            except AuthError:
                failed_attempts += 1
                self.logger.error("Invalid bitbucket auth, try again [%s]", failed_attempts)

    def configure_user_registration(self):
        self.logger.info("Start user registration.")

        aws_lambda = AwsLambda()

        if not self.user_login(aws_lambda):
            bitbucket = self.start_bitbucket_auth()

            self.logger.debug("Connect to bitbucket and get information...")

            # get bitbucket user email which will be used to register user to madcore
            user_email = bitbucket.user.get_primary_email()

            self.logger.info("Check if madcore user already exists: '%s'", user_email)
            user_password = getpass.getpass('Input madcore password: ').decode("utf-8")

            user_data = {
                'email': user_email,
                'password': user_password,
                'created': False,
                'verified': False
            }
            # set user data here so that we have the info in login
            config.set_user_data(user_data)

            # check if user already exists on madcore
            if self.user_login(aws_lambda):
                self.logger.info("User '%s' exists.", user_email)
            else:
                self.logger.info("User does not exists, create: '%s'", user_email)

                while True:
                    try:
                        teams = bitbucket.teams.get_teams_username()
                        break
                    except Exception:
                        self.logger.error("You have no teams into bitbucket account, create one.")
                        input("Press enter when team was created.")

                selected_team = self.single_prompt('team', options=teams, prompt='Select bitbucket team')
                selected_domain = self.single_prompt('domain', options=self.get_allowed_domains(),
                                                     prompt='Select madcore domain')

                team_name = utils.str_to_domain_name(selected_team['team'])
                if team_name != selected_team['team']:
                    self.logger.info("Team name was converted into proper domain name: '%s'", team_name)

                user_sub_domain = '{team_name}.{domain}'.format(team_name=team_name, domain=selected_domain['domain'])

                self.logger.info("The following domain will be configured: '%s'", user_sub_domain)

                user_create_response = aws_lambda.create_user(user_email, user_password, user_sub_domain)

                if user_create_response['created']:
                    self.logger.info("User successfully created.")

                    user_data.update({
                        'domain': selected_domain['domain'],
                        'sub_domain': team_name,
                        'created': True
                    })
                    # at this point we save data into config because we know that user already created on madcore part
                    config.set_user_data(user_data)

                    if not self.verify_user_account(aws_lambda, user_email):
                        self.exit()
                    else:
                        if not self.user_login(aws_lambda):
                            self.exit()
                else:
                    self.logger.error("User was not created.")

        self.logger.info("End user registration.")

    def configure_repos(self, parsed_args):
        self.logger.info("Start cloning all required repos.")

        for repo_name in const.REPO_CLONE:
            self.clone_repo(repo_name, parsed_args)

        self.logger.info("End cloning all required repos.")

    def take_action(self, parsed_args):
        self.log_figlet("Configuration")

        if not os.path.exists(self.config_path):
            inp = "Madcore will now create ~/.madcore folder to store configuration settings. " \
                  "Press enter to begin configuration "
            input(inp)

        self.log_figlet("User Registration")
        self.configure_user_registration()

        self.log_figlet("AWS Configuration")
        self.configure_aws()

        self.log_figlet("Clone repos")
        self.configure_repos(parsed_args)

        self.app.run_subcommand(['status'])
