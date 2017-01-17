from __future__ import print_function

import logging

from madcore.base import PluginsBase
from madcore.configs import config
from madcore.libs.plugins import PluginCommand

logger = logging.getLogger(__name__)


class PluginFunctions(PluginsBase, PluginCommand):
    def get_parser(self, prog_name):
        parser = super(PluginCommand, self).get_parser(prog_name)

        parser.add_argument('plugin_name', choices=self.get_plugin_names(), help='Input plugin name')
        parser.add_argument('function_name', help='Input function name')

        return parser

    def get_function_plugin_parameters(self, plugin_name, function_name):
        plugin_params = self.get_plugin_parameters(plugin_name, function_name)

        if not plugin_params:
            logger.debug("[%s][%s] No plugin command parameters", plugin_name, function_name)
        else:
            logger.info("[%s][%s] Setup plugin command parameters", plugin_name, function_name)
            plugin_params = self.ask_for_plugin_parameters(plugin_params, confirm_default=True)

        return plugin_params or None

    def take_action(self, parsed_args):
        plugin_name = parsed_args.plugin_name
        func_name = parsed_args.function_name

        if not config.is_plugin_installed(plugin_name):
            self.logger.info("[%s] Install plugin first.", plugin_name)
            return 0

        plugin_extra_jobs = self.get_plugin_extra_jobs(plugin_name)

        if not plugin_extra_jobs:
            self.logger.info("[%s] Plugin does not have extra commands.", plugin_name)
            return 0
        else:
            if func_name not in plugin_extra_jobs:
                self.logger.error("[%s] Plugin supports commands: %s", plugin_name, ','.join(plugin_extra_jobs))
                return 0

        job_params = self.get_function_plugin_parameters(plugin_name, func_name)
        job_name = self.get_plugin_job_name(plugin_name, func_name)

        command_run = self.jenkins_run_job_show_output(job_name, parameters=job_params)

        if command_run:
            self.logger.info("[%s][%s] Successfully run plugin command.", plugin_name, func_name)
        else:
            self.logger.error("[%s][%s] Error running plugin command.", plugin_name, func_name)

        return 0
