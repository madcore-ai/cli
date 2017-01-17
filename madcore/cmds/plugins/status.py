from __future__ import print_function

import logging

from madcore.base import PluginsBase
from madcore.configs import config
from madcore.libs.plugins import PluginCommand

logger = logging.getLogger(__name__)


class PluginStatus(PluginsBase, PluginCommand):
    def get_status_install_plugin_parameters(self, plugin_name):
        plugin_params = self.get_plugin_parameters(plugin_name, 'delete')

        if not plugin_params:
            logger.debug("[%s] No plugin status parameters", plugin_name)
        else:
            logger.info("[%s] Setup plugin status parameters", plugin_name)
            plugin_params = self.ask_for_plugin_parameters(plugin_params, confirm_default=True)

        return plugin_params or None

    def take_action(self, parsed_args):
        plugin_name = parsed_args.plugin_name

        if not config.is_plugin_installed(plugin_name):
            self.logger.info("[%s] Install plugin first.", plugin_name)
            return 0

        job_params = self.get_status_install_plugin_parameters(plugin_name)
        job_name = self.get_plugin_status_job_name(plugin_name)

        plugin_status_ok = self.jenkins_run_job_show_output(job_name, parameters=job_params)

        if plugin_status_ok:
            self.logger.info("[%s] Successfully run plugin status.", plugin_name)
        else:
            self.logger.error("[%s] Error running plugin status.", plugin_name)

        return 0
