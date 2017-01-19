from __future__ import print_function, unicode_literals

import logging

from madcore.base import PluginsBase
from madcore.configs import config
from madcore.libs.mixins import PluginCommand

logger = logging.getLogger(__name__)


class PluginRemove(PluginsBase, PluginCommand):
    _description = "Remove madcore plugins"
    plugin_job = 'delete'

    def take_action(self, parsed_args):
        plugin_name = parsed_args.plugin_name

        if not parsed_args.force and not config.is_plugin_installed(plugin_name):
            self.logger.info("[%s] Install plugin first.", plugin_name)
            return 0

        plugin_params = self.get_plugin_job_final_params(plugin_name, 'delete', parsed_args)
        jenkins_params = self.params_to_jenkins_format(plugin_params)

        job_name = self.get_plugin_job_name(plugin_name, self.plugin_job)

        plugin_deleted = self.jenkins_run_job_show_output(job_name, parameters=jenkins_params)

        if plugin_deleted:
            self.logger.info("[%s] Successfully deleted plugin.", plugin_name)
            self.remove_plugin_jobs_params_from_config(plugin_name, parsed_args)
        else:
            self.logger.error("[%s] Error deleting plugin.", plugin_name)

        config.set_plugin_deleted(plugin_name, plugin_deleted)

        return 0
