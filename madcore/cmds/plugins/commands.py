from __future__ import print_function, unicode_literals

import logging

from madcore.configs import config
from madcore.libs.mixins import BasePluginCommand
from madcore.libs.plugins import PluginManagement

logger = logging.getLogger(__name__)


class PluginCustomCommands(PluginManagement, BasePluginCommand):
    _description = "Run specific plugin command"
    _plugin_name = None
    _plugin_job = None

    @property
    def plugin_name(self):
        if not self._plugin_name:
            self._plugin_name = self.get_raw_cmd_args()[0]
        return self._plugin_name

    @property
    def plugin_job(self):
        if not self._plugin_job:
            self._plugin_job = self.get_raw_cmd_args()[1]
        return self._plugin_job

    def get_parser(self, prog_name):
        parser = super(PluginCustomCommands, self).get_parser(prog_name)

        if self.plugin_name in self.get_plugin_names():
            params = self.get_plugin_job_all_params(self.plugin_name, self.plugin_job)
            parser = self.add_params_to_arg_parser(parser, params)

        return parser

    def take_action(self, parsed_args):
        if not config.is_plugin_installed(self.plugin_name):
            self.logger.info("[%s] Install plugin first.", self.plugin_name)
            return 0

        command_run = self.execute_plugin_job(self.plugin_name, self.plugin_job, parsed_args)

        if command_run:
            self.logger.info("[%s][%s] OK.", self.plugin_name, self.plugin_job)
        else:
            self.logger.error("[%s][%s] Error running plugin command.", self.plugin_name, self.plugin_job)

        return 0
