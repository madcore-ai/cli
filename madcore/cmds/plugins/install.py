from __future__ import print_function, unicode_literals

import logging

from madcore.configs import config
from madcore.libs.mixins import PluginCommand
from madcore.libs.plugins import PluginManagement

logger = logging.getLogger(__name__)


class PluginInstall(PluginManagement, PluginCommand):
    _description = "Install madcore plugins"
    plugin_job = 'deploy'
    _plugin_name = None

    @property
    def plugin_name(self):
        if not self._plugin_name:
            self._plugin_name = self.get_plugin_name_from_input_args()
        return self._plugin_name

    def get_parser(self, prog_name):
        parser = super(PluginInstall, self).get_parser(prog_name)

        if self.plugin_name in self.get_plugin_names():
            params = self.get_plugin_job_all_params(self.plugin_name, self.plugin_job)
            parser = self.add_params_to_arg_parser(parser, params)

        return parser

    def take_action(self, parsed_args):
        plugin_name = parsed_args.plugin_name

        # after plugin was installed. Currently we need to exit the cli interactive mode to see the new commands
        if not parsed_args.force and config.is_plugin_installed(plugin_name):
            self.logger.info("[%s] Plugin already installed.", plugin_name)
            return 0

        plugin_installed = self.execute_plugin_job(plugin_name, self.plugin_job, parsed_args)
        config.set_plugin_installed(plugin_name, plugin_installed)

        if parsed_args.force or plugin_installed:
            self.app.plugin_loader.load_installed_plugins_commands(plugin_name)
            self.logger.info("[%s] Successfully installed plugin.", plugin_name)
        else:
            self.logger.error("[%s] Error installing plugin.", plugin_name)

        return 0
