from __future__ import unicode_literals, print_function

import logging

from madcore.base import PluginsBase
from madcore.cmds.plugins.commands import PluginCustomCommands
from madcore.configs import config

logger = logging.getLogger(__name__)


class PluginLoader(PluginsBase):
    def __init__(self, command_manager):
        self.command_manager = command_manager

    def load_installed_plugins_commands(self):
        for plugin_name in self.get_plugin_names():
            if config.is_plugin_installed(plugin_name):
                for job_name in self.get_plugin_extra_jobs(plugin_name):
                    command_name = '%s %s' % (plugin_name, job_name)
                    logger.debug("Load plugin command: '%s'" % command_name)

                    # str(command_name) is required because cmd module gives error otherwise
                    # when we are using from __future__ import unicode_literals
                    self.command_manager.add_command(str(command_name), PluginCustomCommands)
