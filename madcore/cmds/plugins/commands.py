from __future__ import print_function, unicode_literals

import logging

from madcore.base import PluginsBase
from madcore.configs import config
from madcore.libs.mixins import BasePluginCommand

logger = logging.getLogger(__name__)


class PluginCustomCommands(PluginsBase, BasePluginCommand):
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
                default=job_param['value'],
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

        plugin_params = self.get_plugin_job_final_params(plugin_name, plugin_command_name, parsed_args)
        jenkins_params = self.params_to_jenkins_format(plugin_params)

        job_name = self.get_plugin_job_name(plugin_name, plugin_command_name)

        command_run = self.jenkins_run_job_show_output(job_name, parameters=jenkins_params)

        if command_run:
            self.logger.info("[%s][%s] Successfully run plugin command.", plugin_name, plugin_command_name)
            self.set_plugin_jobs_params_to_config(plugin_name, plugin_command_name, plugin_params, parsed_args)
        else:
            self.logger.error("[%s][%s] Error running plugin command.", plugin_name, plugin_command_name)

        return 0
