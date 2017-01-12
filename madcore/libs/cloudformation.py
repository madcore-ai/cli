from __future__ import print_function, unicode_literals

import sys

import boto3
from cliff.formatters.table import TableFormatter

from madcore import const
from madcore import utils
from madcore.base import CloudFormationBase
from madcore.base import Stdout
from madcore.configs import config
from madcore.libs.aws import AwsLambda
from madcore.logs import logging


class StackCreate(CloudFormationBase):
    log = logging.getLogger(__name__)

    def __init__(self, app, *args, **kwargs):
        super(StackCreate, self).__init__(*args, **kwargs)
        self.app = app
        self.formatter = TableFormatter()

    def produce_output(self, parsed_args, column_names, data):
        self.formatter.emit_list(column_names, data, Stdout(), parsed_args)

    def stack_show_output_parameters(self, stack_details, parsed_args):
        def show_output(results_key, column_names):
            data = []

            if results_key in stack_details:
                for param in stack_details[results_key]:
                    data.append([param.get(c, '') for c in column_names])

                self.produce_output(parsed_args, column_names, data)

        self.log.info("Output parameters for stack '{StackName}':".format(**stack_details))
        show_output('Outputs', ['OutputKey', 'OutputValue', 'Description'])

    def stack_show_input_parameter(self, stack_short_name, input_params, parsed_args):
        stack_name = self.stack_name(stack_short_name)

        def show_output(column_names):
            data = []

            for param in input_params:
                data.append([param[c] for c in column_names])

            self.produce_output(parsed_args, column_names, data)

        if input_params != [{}]:
            self.log.info("Input parameters for stack '{}':".format(stack_name))
            show_output(['ParameterKey', 'ParameterValue'])
        else:
            self.log.info("No input parameters for stack '{}'.".format(stack_name))

    def create_stack(self, stack_short_name, input_parameters, capabilities=None, show_progress=True):
        stack_name = self.stack_name(stack_short_name)
        template_file = '%s.json' % stack_short_name.lower()

        if not input_parameters:
            input_parameters = [{}]

        response = self.cf_client.create_stack(
            StackName=stack_name,
            TemplateBody=self.get_template_local(template_file),
            Parameters=input_parameters,
            Capabilities=capabilities or []
        )

        if show_progress:
            self.show_stack_create_events_progress(stack_name)

        return response

    def create_stack_if_not_exists(self, stack_short_name, input_parameters, parsed_args, capabilities=None):
        exists = False
        stack_name = self.stack_name(stack_short_name)

        self.stack_show_input_parameter(stack_short_name, input_parameters, parsed_args)

        stack_details = self.get_stack(stack_name)

        if stack_details is None:
            self.log.info("Stack '%s' does not exists, creating it..." % stack_name)
            self.create_stack(stack_short_name, input_parameters, capabilities=capabilities)
            stack_details = self.get_stack(stack_name)
            self.log.info("Stack '%s' created.\n" % stack_name)
        else:
            self.log.info("Stack '%s' already exists, skip." % stack_name)
            exists = True

        self.stack_show_output_parameters(stack_details, parsed_args)

        return stack_details, exists

    @classmethod
    def create_stack_parameters(cls, dict_params={}):
        cf_params = []

        if not dict_params:
            cf_params.append({})
        else:
            for param_key, param_value in dict_params.iteritems():
                cf_params.append({
                    'ParameterKey': param_key,
                    'ParameterValue': param_value
                })

        return cf_params

    def get_hosted_zone_name_servers(self, zone_id):
        client = boto3.client('route53', **self.get_aws_connection_params)
        zone = client.get_hosted_zone(Id=zone_id)

        return zone['DelegationSet']['NameServers']

    def take_action(self, parsed_args):
        # create S3
        s3_params = self.create_stack_parameters(dict_params={})
        s3_stack, s3_exists = self.create_stack_if_not_exists('s3', s3_params, parsed_args)

        # create Network
        network_parameters = {
            'Type': 'Production',
            'Env': 'madcore',
            'VPCCIDRBlock': '10.99.0.0/16'
        }
        network_params = self.create_stack_parameters(dict_params=network_parameters)
        network_stack, network_exists = self.create_stack_if_not_exists('network', network_params, parsed_args)

        # create SGFM
        sgfm_parameters = {
            'FollowMeIpAddress': self.get_ipv4(),
            'VpcId': self.get_output_from_dict(network_stack['Outputs'], 'VpcId')
        }
        sgfm_params = self.create_stack_parameters(dict_params=sgfm_parameters)
        sgfm_stack, sgfm_exists = self.create_stack_if_not_exists('sgfm', sgfm_params, parsed_args)

        # create Core
        aws_config = config.get_aws_data()
        core_parameters = {
            'FollowmeSecurityGroup': self.get_output_from_dict(sgfm_stack['Outputs'], 'FollowmeSgId'),
            'PublicNetZoneA': self.get_output_from_dict(network_stack['Outputs'], 'PublicNetZoneA'),
            'S3BucketName': self.get_output_from_dict(s3_stack['Outputs'], 'S3BucketName'),
            'KeyName': aws_config['key_name'],
            'InstanceType': aws_config['instance_type']
        }
        core_params = self.create_stack_parameters(dict_params=core_parameters)
        core_capabilities = ["CAPABILITY_IAM"]
        core_stack, core_exists = self.create_stack_if_not_exists('core', core_params, parsed_args,
                                                                  capabilities=core_capabilities)
        # create DNS
        user_config = config.get_user_data()
        dns_parameters = {
            'DomainName': user_config['domain'],
            'SubDomainName': user_config['sub_domain'],
            'EC2PublicIP': self.get_output_from_dict(core_stack['Outputs'], 'MadCorePublicIp'),
        }
        dns_params = self.create_stack_parameters(dict_params=dns_parameters)
        dns_stack, dns_exists = self.create_stack_if_not_exists('dns', dns_params, parsed_args)

        # do DNS delegation
        if not config.is_dns_delegated:
            self.log.info("DNS delegation start")
            aws_lambda = AwsLambda()
            name_servers = self.get_hosted_zone_name_servers(
                self.get_output_from_dict(dns_stack['Outputs'], 'HostedZoneID'))

            delegation_response = aws_lambda.dns_delegation(name_servers)

            if delegation_response.get('verified', False):
                self.log.info("DNS delegation verified.")
                dns_delegation = True
                config.set_user_data({'dns_delegation': True})
            else:
                self.log.error("DNS delegation error: %s" % delegation_response)
                dns_delegation = False

            config.set_user_data({'dns_delegation': dns_delegation})
            self.log.info("DNS delegation end.")

            if not dns_delegation:
                self.log.error("EXIT.")
                sys.exit(1)

            self.log.info("Wait until DNS for domain '%s' is updated..." % config.get_full_domain())
            if utils.hostname_resolves(config.get_full_domain()):
                self.log.info("DNS updated.")
            else:
                self.log.error("Error while updating DNS.")
        else:
            self.log.info("DNS delegation already setup.")

        # create Cluster
        # cluster_parameters = {
        #     'VpcId': self.get_output_from_dict(network_stack['Outputs'], 'VpcId'),
        #     'PublicNetZoneA': self.get_output_from_dict(network_stack['Outputs'], 'PublicNetZoneA'),
        #     'MasterIP': self.get_output_from_dict(core_stack['Outputs'], 'MadCorePrivateIp'),
        #     'S3BucketName': self.get_output_from_dict(s3_stack['Outputs'], 'S3BucketName')
        # }
        # cluster_params = self.create_stack_parameters(dict_params=cluster_parameters)
        # cluster_capabilities = ["CAPABILITY_IAM"]
        # _, cluster_exists = self.create_stack_if_not_exists('cluster', cluster_params, parsed_args,
        #                                                     capabilities=cluster_capabilities)
        self.log.info("Stack Create status:")
        self.produce_output(parsed_args,
                            ('StackName', 'Created'),
                            (
                                (const.STACK_S3, not s3_exists),
                                (const.STACK_NETWORK, not network_exists),
                                (const.STACK_FOLLOWME, not sgfm_exists),
                                (const.STACK_CORE, not core_exists),
                                (const.STACK_DNS, not dns_exists)
                                # (const.STACK_CLUSTER, not cluster_exists)
                            )
                            )
