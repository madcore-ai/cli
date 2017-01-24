from __future__ import print_function, unicode_literals

import logging

from madcore.configs import config
from madcore.libs.mixins import PluginCommand
from madcore.libs.plugins import PluginManagement

logger = logging.getLogger(__name__)


class PluginRemove(PluginManagement, PluginCommand):
    _description = "Remove madcore plugins"
    plugin_job = 'delete'

    def take_action(self, parsed_args):
        plugin_name = parsed_args.plugin_name

        if not parsed_args.force and not config.is_plugin_installed(plugin_name):
            self.logger.info("[%s] Install plugin first.", plugin_name)
            return 0

        plugin_deleted = self.execute_plugin_job(plugin_name, self.plugin_job, parsed_args)
        config.set_plugin_deleted(plugin_name, parsed_args.force or plugin_deleted)

        if parsed_args.force or plugin_deleted:
            self.remove_plugin_jobs_params_from_config(plugin_name)
            self.app.plugin_loader.unload_removed_plugins_commands(plugin_name)
            self.logger.info("[%s] Successfully deleted plugin.", plugin_name)
        else:
            self.logger.error("[%s] Error deleting plugin.", plugin_name)

        return 0
