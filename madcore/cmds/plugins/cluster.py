from __future__ import print_function, unicode_literals

import argparse
import logging

from madcore.libs.mixins import BasePluginCommand
from madcore.libs.plugins import PluginManagement

logger = logging.getLogger(__name__)


class PluginClusterExtendBy(PluginManagement, BasePluginCommand):
    _description = "Extend cluster by <nodes>"

    @property
    def plugin_name(self):
        return self.cmd_name.split()[0]

    @property
    def plugin_command_name(self):
        return self.cmd_name.split()[-1]

    @classmethod
    def positive_integer_validator(cls, val):
        try:
            val = int(val)
            if not int(val) > 0:
                raise
            return val
        except:
            raise argparse.ArgumentTypeError("Allow positive integers only.")

    def get_parser(self, prog_name):
        parser = super(PluginClusterExtendBy, self).get_parser(prog_name)

        parser.add_argument('extend_by', default=1, help="Extend cluster by specific number of nodes",
                            type=self.positive_integer_validator)

        return parser

    def update_cluster_nodes(self, nodes_nr):
        plugin = self.get_plugin_by_name(self.plugin_name)
        cf = plugin['cloudformations'][0]

        stack_details = self.get_stack(cf['stack_name'])

        if not stack_details:
            self.logger.error("Cluster not created.")
            self.exit()

        stack_outputs = self.stack_output_to_dict(stack_details)

        self.change_stack_output(stack_outputs, nodes_nr)

        template = self.get_plugin_template_file(self.plugin_name, cf['template_file'])
        self.update_stack_if_changed(cf['stack_name'], template, stack_details, stack_outputs,
                                     capabilities=cf['capabilities'])

    def change_stack_output(self, stack_outputs, nodes_nr):
        for output_key, output_val in stack_outputs.items():
            output_val = int(output_val)
            new_value = output_val + nodes_nr
            stack_outputs[output_key] = str(new_value)

        return stack_outputs

    def take_action(self, parsed_args):
        self.update_cluster_nodes(parsed_args.extend_by)

        return 0


class PluginClusterContractBy(PluginClusterExtendBy):
    _description = "Contract cluster by <nodes>"

    def get_parser(self, prog_name):
        parser = super(PluginClusterExtendBy, self).get_parser(prog_name)

        parser.add_argument('contract_by', default=1, help="Contract cluster by specific number of nodes",
                            type=self.positive_integer_validator)

        return parser

    def change_stack_output(self, stack_outputs, nodes_nr):
        for output_key, output_val in stack_outputs.items():
            output_val = int(output_val)
            if output_val == 0:
                self.logger.error("Can't contract by: %s, cluster does not have nodes.", nodes_nr)
                self.exit()
            new_value = output_val - nodes_nr
            if new_value < 0:
                self.logger.error("Can't contract by: %s, cluster does have '%s' nodes.", nodes_nr, output_val)
                self.exit()
            stack_outputs[output_key] = str(new_value)

        return stack_outputs

    def take_action(self, parsed_args):
        self.update_cluster_nodes(parsed_args.contract_by)

        return 0


class PluginClusterZero(PluginClusterExtendBy):
    _description = "Reset cluster nodes to zero"

    def get_parser(self, prog_name):
        parser = super(PluginClusterExtendBy, self).get_parser(prog_name)

        parser.add_argument('zero', action='store_true', help="Reset cluster nodes to zero")

        return parser

    def change_stack_output(self, stack_outputs, nodes_nr):
        for output_key, output_val in stack_outputs.items():
            stack_outputs[output_key] = str(nodes_nr)

        return stack_outputs

    def take_action(self, parsed_args):
        self.update_cluster_nodes(0)

        return 0
