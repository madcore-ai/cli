from __future__ import print_function, unicode_literals

import json
import logging

from cliff.lister import Lister

import const
from base import CloudFormationBase


class StackCreate(CloudFormationBase, Lister):
    _description = "Create stacks"

    log = logging.getLogger(__name__)

    def load_parameters_file(self, stack_short_name):
        params_file = self.get_template_local('%s-parameters.json' % stack_short_name)
        input_params = json.loads(params_file)

        return input_params

    def stack_show_output_parameters(self, stack_details, parsed_args):
        def show_output(results_key, column_names):
            data = []

            if results_key in stack_details:
                for param in stack_details[results_key]:
                    data.append([param.get(c, '') for c in column_names])

                self.produce_output(parsed_args, column_names, data)

        self.log.info("\nOutput parameters for stack '{StackName}':".format(**stack_details))
        show_output('Outputs', ['OutputKey', 'OutputValue', 'Description'])

    def stack_show_input_parameter(self, stack_short_name, input_params, parsed_args):
        stack_name = self.stack_name(stack_short_name)

        def show_output(column_names):
            data = []

            for param in input_params:
                data.append([param[c] for c in column_names])

            self.produce_output(parsed_args, column_names, data)

        if input_params != [{}]:
            self.log.info("\nInput parameters for stack '{}':".format(stack_name))
            show_output(['ParameterKey', 'ParameterValue'])
        else:
            self.log.info("\nNo input parameters for stack '{}'.".format(stack_name))

    def create_stack(self, stack_short_name, input_parameters, capabilities=None, show_progress=True):
        stack_name = self.stack_name(stack_short_name)
        template_file = '%s.json' % stack_short_name.lower()

        if not input_parameters:
            input_parameters = [{}]

        response = self.client.create_stack(
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
            self.log.info("Stack '%s' created." % stack_name)
        else:
            self.log.info("Stack '%s' already exists, skip." % stack_name)
            exists = True

        self.stack_show_output_parameters(stack_details, parsed_args)

        return stack_details, exists

    def create_stack_parameters(self, stack_short_name, override_params=None):
        input_params = self.load_parameters_file(stack_short_name)

        if not override_params:
            return input_params
        else:
            for param in input_params:
                if param['ParameterKey'] in override_params:
                    param['ParameterValue'] = override_params[param['ParameterKey']]

        return input_params

    def take_action(self, parsed_args):
        # create S3
        s3_params = self.create_stack_parameters('s3')
        s3_stack, s3_exists = self.create_stack_if_not_exists('s3', s3_params, parsed_args)

        # create Network
        network_params = self.create_stack_parameters('network')
        network_stack, network_exists = self.create_stack_if_not_exists('network', network_params, parsed_args)

        # create SGFM
        sgfm_override_parameters = {
            'FollowMeIpAddress': self.get_ipv4(),
            'VpcId': self.get_output_from_dict(network_stack['Outputs'], 'VpcId')
        }
        sgfm_params = self.create_stack_parameters('sgfm', sgfm_override_parameters)
        sgfm_stack, sgfm_exists = self.create_stack_if_not_exists('sgfm', sgfm_params, parsed_args)

        # create Core
        core_override_parameters = {
            'FollowmeSecurityGroup': self.get_output_from_dict(sgfm_stack['Outputs'], 'FollowmeSgId'),
            'PublicNetZoneA': self.get_output_from_dict(network_stack['Outputs'], 'PublicNetZoneA'),
            'S3BucketName': self.get_output_from_dict(s3_stack['Outputs'], 'S3BucketName'),
            'KeyName': self.settings['aws']['KeyName'],
            'InstanceType': self.settings['aws']['InstanceType']
        }
        core_params = self.create_stack_parameters('core', core_override_parameters)
        core_capabilities = ["CAPABILITY_IAM"]
        core_stack, core_exists = self.create_stack_if_not_exists('core', core_params, parsed_args,
                                                                  capabilities=core_capabilities)

        # create DNS
        dns_override_parameters = {
            'EC2PublicIP': self.get_output_from_dict(core_stack['Outputs'], 'MadCorePublicIp'),
        }
        dns_params = self.create_stack_parameters('dns', dns_override_parameters)
        dns_stack, dns_exists = self.create_stack_if_not_exists('dns', dns_params, parsed_args)

        # create Cluster
        # cluster_override_parameters = {
        #     'VpcId': self.get_output_from_dict(network_stack['Outputs'], 'VpcId'),
        #     'PublicNetZoneA': self.get_output_from_dict(network_stack['Outputs'], 'PublicNetZoneA'),
        #     'MasterIP': self.get_output_from_dict(core_stack['Outputs'], 'MadCorePrivateIp'),
        #     'S3BucketName': self.get_output_from_dict(s3_stack['Outputs'], 'S3BucketName')
        # }
        # cluster_params = self.create_stack_parameters('cluster', cluster_override_parameters)
        # cluster_capabilities = ["CAPABILITY_IAM"]
        # _, cluster_exists = self.create_stack_if_not_exists('cluster', cluster_params, parsed_args,
        #                                                     capabilities=cluster_capabilities)
        self.log.info("\nStack Create status:")

        return (
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
