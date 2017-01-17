import ConfigParser
import json
import logging
import os
import time

import boto3
import botocore.exceptions
from botocore import UNSIGNED
from botocore.client import Config

from madcore import const
from madcore.configs import config

logger = logging.getLogger(__name__)


class AwsConfig(object):
    def __init__(self, config_path=None):
        self.config = self.load_config(config_path)

    @classmethod
    def load_config(cls, config_path=None):
        config_path = config_path or os.path.join(os.path.expanduser("~"), '.aws/config')
        cfg = ConfigParser.ConfigParser()
        cfg.read(config_path)

        return cfg

    def get_regions(self):
        regions = []
        for section in self.config.sections():
            regions.append(self.config.get(section, 'region'))

        return regions


class AwsLambda(object):
    def __init__(self, identity_pool_id=None):
        # region name for the base account
        self.region_name = 'eu-west-1'

        self.identity_pool_id = identity_pool_id or const.AWS_IDENTITY_POOL_ID
        self.cognito_client = boto3.client('cognito-identity', region_name=self.region_name,
                                           config=Config(signature_version=UNSIGNED))
        self.lambda_client_no_auth = self.create_aws_lambda_client()

    @classmethod
    def get_account_id(cls):
        return boto3.client('sts').get_caller_identity()["Account"]

    def get_identity_id(self):
        identity_id = config.get_aws_identity_id()

        account_id = self.get_account_id()

        if identity_id is None:
            response = self.cognito_client.get_id(
                AccountId=account_id,
                IdentityPoolId=self.identity_pool_id,
            )
            identity_id = response['IdentityId']
            config.set_aws_identity_id(identity_id)

        return identity_id

    def create_aws_lambda_client(self):
        identity_id = self.get_identity_id()

        response = self.cognito_client.get_credentials_for_identity(
            IdentityId=identity_id
        )

        credentials = response['Credentials']

        credentials = {
            'aws_access_key_id': credentials['AccessKeyId'],
            'aws_secret_access_key': credentials['SecretKey'],
            'aws_session_token': credentials['SessionToken'],
            'region_name': self.region_name
        }
        client = boto3.client('lambda', **credentials)

        return client

    def create_aws_lambda_client_auth(self):
        user_data = config.get_user_data()

        while True:
            login_data = config.get_login_data()
            identity_id = login_data['identityid']

            try:
                response = self.cognito_client.get_credentials_for_identity(
                    IdentityId=identity_id,
                    Logins={'cognito-identity.amazonaws.com': login_data['token']}
                )
                credentials = response['Credentials']
                # TODO@geo we may need to save this expiration and check whether to login again
                # logger.debug(response['Credentials']['Expiration'])

                credentials = {
                    'aws_access_key_id': credentials['AccessKeyId'],
                    'aws_secret_access_key': credentials['SecretKey'],
                    'aws_session_token': credentials['SessionToken'],
                    'region_name': self.region_name
                }
                client = boto3.client('lambda', **credentials)

                return client
            except botocore.exceptions.ClientError as error:
                logger.error(error)
                if 'Token is expired' in str(error):
                    logger.debug('Token is expired, login.')
                    login_response = self.auth_login(user_data['email'], user_data['password'])
                    if login_response['login']:
                        logger.info("Successfully logged in.")
                        config.set_login_data(login_response)
                    else:
                        logger.error("Invalid login, try again")
                        time.sleep(5)

    def verify_user(self, email, verify_code):
        payload = {
            'email': email,
            'verify': verify_code
        }

        response = self.lambda_client_no_auth.invoke(
            FunctionName='LambdAuthVerifyUser',
            InvocationType='RequestResponse',
            LogType='Tail',
            Payload=json.dumps(payload)
        )

        return json.loads(response['Payload'].read())

    def create_user(self, email, password, domain):
        payload = {
            'email': email,
            'password': password,
            'domain': domain
        }
        response = self.lambda_client_no_auth.invoke(
            FunctionName='LambdAuthCreateUser',
            InvocationType='RequestResponse',
            LogType='Tail',
            Payload=json.dumps(payload)
        )

        return json.loads(response['Payload'].read())

    def auth_login(self, email, password):
        payload = {
            'email': email,
            'password': password,
        }
        response = self.lambda_client_no_auth.invoke(
            FunctionName='LambdAuthLogin',
            InvocationType='RequestResponse',
            LogType='Tail',
            Payload=json.dumps(payload)
        )

        return json.loads(response['Payload'].read())

    def dns_delegation(self, nameservers):
        lambda_client_auth = self.create_aws_lambda_client_auth()

        user_data = config.get_user_data()
        aws_data = config.get_aws_data()

        session = boto3.Session(region_name=aws_data['region_name'])
        account_id = session.client('sts').get_caller_identity()["Account"]

        payload = {
            'email': user_data['email'],
            'password': user_data['password'],
            'subdomain': user_data['sub_domain'],
            'domain': user_data['domain'],
            'region': aws_data['region_name'],
            'awsid': account_id,
        }

        for i, name_server in enumerate(nameservers, 1):
            payload['dns%s' % i] = name_server

        response = lambda_client_auth.invoke(
            FunctionName='LambdSendDNSValues',
            InvocationType='RequestResponse',
            LogType='Tail',
            Payload=json.dumps(payload)
        )

        return json.loads(response['Payload'].read())

    def lost_password(self, email):
        payload = {
            'email': email,
        }
        response = self.lambda_client_no_auth.invoke(
            FunctionName='LambdAuthLostPassword',
            InvocationType='RequestResponse',
            LogType='Tail',
            Payload=json.dumps(payload)
        )

        return json.loads(response['Payload'].read())

    def reset_password(self, email, token, new_password):
        payload = {
            'email': email,
            'lostToken': token,
            'newPassword': new_password
        }
        response = self.lambda_client_no_auth.invoke(
            FunctionName='LambdAuthResetPassword',
            InvocationType='RequestResponse',
            LogType='Tail',
            Payload=json.dumps(payload)
        )

        return json.loads(response['Payload'].read())
