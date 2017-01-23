from __future__ import print_function, unicode_literals

import logging

from madcore.configs import config
from madcore.libs.mixins import BasePluginCommand
from madcore.libs.plugins import PluginManagement

logger = logging.getLogger(__name__)


class PluginCustomCommands(PluginManagement, BasePluginCommand):
    _description = "Run specific plugin command"

    @property
    def plugin_name(self):
        return self.cmd_name.split()[0]

    @property
    def plugin_command_name(self):
        return self.cmd_name.split()[-1]

    def get_parser(self, prog_name):
        parser = super(PluginCustomCommands, self).get_parser(prog_name)

        plugin_command_params = self.get_plugin_job_parameters(self.plugin_name, self.plugin_command_name,
                                                               check_config=False)

        # TODO@geo change help here to param description
        # Here we save all the user input params with '_' prefix to not get conflicted with the cli defined ones
        for job_param in plugin_command_params:
            parser.add_argument(
                '--%s' % job_param['name'],
                dest='_%s' % job_param['name'],
                type=job_param['validator'],
                help=job_param['description'],
            )

        return parser

    def take_action(self, parsed_args):
        plugin_name = self.plugin_name
        plugin_command_name = self.plugin_command_name

        if not config.is_plugin_installed(plugin_name):
            self.logger.info("[%s] Install plugin first.", plugin_name)
            return 0

        command_run = self.execute_plugin_job(plugin_name, plugin_command_name, parsed_args)

        if command_run:
            self.logger.info("[%s][%s] OK.", plugin_name, plugin_command_name)
        else:
            self.logger.error("[%s][%s] Error running plugin command.", plugin_name, plugin_command_name)

        return 0
