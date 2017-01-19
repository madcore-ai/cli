from __future__ import print_function, unicode_literals

import logging

from madcore.base import PluginsBase
from madcore.configs import config
from madcore.libs.mixins import PluginCommand

logger = logging.getLogger(__name__)


class PluginInstall(PluginsBase, PluginCommand):
    _description = "Install madcore plugins"
    plugin_job = 'deploy'

    def take_action(self, parsed_args):
        plugin_name = parsed_args.plugin_name

        if not parsed_args.force and config.is_plugin_installed(plugin_name):
            self.logger.info("[%s] Plugin already installed.", plugin_name)
            return 0

        plugin_params = self.get_plugin_job_final_params(plugin_name, 'deploy', parsed_args)
        jenkins_params = self.params_to_jenkins_format(plugin_params)

        job_name = self.get_plugin_job_name(plugin_name, self.plugin_job)

        plugin_installed = self.jenkins_run_job_show_output(job_name, parameters=jenkins_params)

        if plugin_installed:
            self.logger.info("[%s] Successfully installed plugin.", plugin_name)
            self.set_plugin_jobs_params_to_config(plugin_name, self.plugin_job, plugin_params, parsed_args)
        else:
            self.logger.error("[%s] Error installing plugin.", plugin_name)

        config.set_plugin_installed(plugin_name, plugin_installed)

        return 0
