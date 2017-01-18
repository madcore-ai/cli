from __future__ import print_function

import logging

from madcore.base import PluginsBase, JenkinsBase
from madcore.configs import config
from madcore.libs.mixins import BasePluginCommand

logger = logging.getLogger(__name__)


class PluginCustomCommands(PluginsBase, JenkinsBase, BasePluginCommand):
    _description = "Run specific plugin command"

    @property
    def plugin_name(self):
        return self.cmd_name.split()[0]

    @property
    def plugin_command_name(self):
        return self.cmd_name.split()[-1]

    def get_parser(self, prog_name):
        parser = super(PluginCustomCommands, self).get_parser(prog_name)

        plugin_command_params = self.get_plugin_parameters(self.plugin_name, self.plugin_command_name)

        # TODO@geo change help here to param description
        # Here we save all the user input params with _param_name to not get conflicted with the app defined ones
        if plugin_command_params:
            for param_key, param_value in plugin_command_params.items():
                parser.add_argument('--%s' % param_key, default=param_value, dest='_%s' % param_key,
                                    help="Input '%s' parameter." % param_key)

        return parser

    def get_command_plugin_parameters(self, plugin_name, command_name, parsed_args):
        plugin_params = self.get_plugin_parameters(plugin_name, command_name)

        if not plugin_params:
            logger.debug("[%s][%s] No plugin command parameters", plugin_name, command_name)
        else:
            logger.info("[%s][%s] Setup plugin command parameters", plugin_name, command_name)
            plugin_params = self.ask_for_plugin_parameters(plugin_params, parsed_args)

        return plugin_params or None

    def take_action(self, parsed_args):
        plugin_name = self.plugin_name
        plugin_command_name = self.plugin_command_name

        if not config.is_plugin_installed(plugin_name):
            self.logger.info("[%s] Install plugin first.", plugin_name)
            return 0

        job_params = self.get_command_plugin_parameters(plugin_name, plugin_command_name, parsed_args)
        job_name = self.get_plugin_job_name(plugin_name, plugin_command_name)

        command_run = self.jenkins_run_job_show_output(job_name, parameters=job_params)

        if command_run:
            self.logger.info("[%s][%s] Successfully run plugin command.", plugin_name, plugin_command_name)
        else:
            self.logger.error("[%s][%s] Error running plugin command.", plugin_name, plugin_command_name)

        return 0
