from __future__ import print_function

import logging

from madcore.base import PluginsBase
from madcore.configs import config
from madcore.libs.plugins import PluginCommand

logger = logging.getLogger(__name__)


class PluginDelete(PluginsBase, PluginCommand):
    def get_delete_install_plugin_parameters(self, plugin_name):
        plugin_params = self.get_plugin_parameters(plugin_name, 'delete')

        if not plugin_params:
            logger.debug("[%s] No plugin delete parameters", plugin_name)
        else:
            logger.info("[%s] Setup plugin delete parameters", plugin_name)
            plugin_params = self.ask_for_plugin_parameters(plugin_params, confirm_default=True)

        return plugin_params or None

    def take_action(self, parsed_args):
        plugin_name = parsed_args.plugin_name

        if not config.is_plugin_installed(plugin_name):
            self.logger.info("[%s] Install plugin first.", plugin_name)
            return 0

        job_params = self.get_delete_install_plugin_parameters(plugin_name)
        job_name = self.get_plugin_delete_job_name(plugin_name)

        plugin_deleted = self.jenkins_run_job_show_output(job_name, parameters=job_params)

        if plugin_deleted:
            self.logger.info("[%s] Successfully deleted plugin.", plugin_name)
        else:
            self.logger.error("[%s] Error deleting plugin.", plugin_name)

        config.set_plugin_deleted(plugin_name, plugin_deleted)

        return 0
