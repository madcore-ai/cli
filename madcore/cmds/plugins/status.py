from __future__ import print_function, unicode_literals

import logging

from madcore.configs import config
from madcore.libs.mixins import PluginCommand
from madcore.libs.plugins import PluginManagement

logger = logging.getLogger(__name__)


class PluginStatus(PluginManagement, PluginCommand):
    _description = "Show status of madcore plugins"
    plugin_job = 'status'

    def take_action(self, parsed_args):
        plugin_name = parsed_args.plugin_name

        if not config.is_plugin_installed(plugin_name):
            self.logger.info("[%s] Install plugin first.", plugin_name)
            return 0

        self.execute_plugin_job(plugin_name, self.plugin_job, parsed_args)

        return 0
