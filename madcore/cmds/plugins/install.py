from __future__ import print_function

import logging

from madcore.base import PluginsBase, JenkinsBase
from madcore.libs.mixins import PluginCommand
from madcore.configs import config

logger = logging.getLogger(__name__)


class PluginInstall(PluginsBase, JenkinsBase, PluginCommand):
    _description = "Install madcore plugins"

    def get_setup_install_plugin_parameters(self, plugin_name, parsed_args):
        plugin_params = self.get_plugin_parameters(plugin_name, 'deploy')

        if not plugin_params:
            logger.debug("[%s] No plugin install parameters", plugin_name)
        else:
            logger.info("[%s] Setup plugin install parameters", plugin_name)
            plugin_params = self.ask_for_plugin_parameters(plugin_params, parsed_args)

        return plugin_params or None

    def take_action(self, parsed_args):
        plugin_name = parsed_args.plugin_name

        if config.is_plugin_installed(plugin_name):
            self.logger.info("[%s] Plugin already installed.", plugin_name)
            return 0

        job_params = self.get_setup_install_plugin_parameters(plugin_name, parsed_args)
        job_name = self.get_plugin_deploy_job_name(plugin_name)

        plugin_installed = self.jenkins_run_job_show_output(job_name, parameters=job_params)

        if plugin_installed:
            self.logger.info("[%s] Successfully installed plugin.", plugin_name)
        else:
            self.logger.error("[%s] Error installing plugin.", plugin_name)

        config.set_plugin_installed(plugin_name, plugin_installed)

        return 0
