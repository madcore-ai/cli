import os
import sys
import logging
from cliff.app import App
from cliff.commandmanager import CommandManager
from cliff.command import Command
from cliff.show import ShowOne
from cliff.lister import Lister
import urllib3
import boto3


class CoreFollowme(ShowOne):
    """Show a list of files in the current directory.

    The file name and size are printed by default.
    """

    log = logging.getLogger(__name__)

    def get_ipv4(self):
        http = urllib3.PoolManager()
        r = http.request('GET', 'http://ipv4.icanhazip.com/')
        if r.status is not 200:
            raise RuntimeError('No Internet')
        return r.data

    def get_from_dict(self, dic):
        return next(i for i in dic if i['ParameterKey'] == 'FollowMeIpAddress')['ParameterValue']

    def get_stack_followme(self):
        cf = boto3.client('cloudformation')
        r = cf.describe_stacks(
                StackName='MADCORE-FollowMe'
        )
        return r['Stacks'][0]

    def take_action(self, parsed_args):
        ipv4 = self.get_ipv4()
        self.log.info('Core Followme: Your public IP detected as: {0}'.format(ipv4))
        stack = self.get_stack_followme()
        previous_parameters = stack['Parameters']
        ipv4_previous = self.get_from_dict(previous_parameters)
        columns = ('New IPv4',
            'Stack ID',
            'Previous IPv4'
                   )
        data = (''.join(ipv4.split()),
                stack['StackId'],
                ipv4_previous
                )
        return (columns, data)


class Error(Command):
    "Always raises an error"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info('causing error')
        raise RuntimeError('this is the expected exception')