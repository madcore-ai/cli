from __future__ import unicode_literals, print_function

import logging

from madcore.base import PluginsBase
from madcore.cmds.plugins.commands import PluginCustomCommands
from madcore.configs import config

logger = logging.getLogger(__name__)


class PluginLoader(PluginsBase):
    # define here custom commands for cluster
    PLUGIN_CLUSTER_COMMANDS = {
    }

    def __init__(self, command_manager):
        self.command_manager = command_manager

    def load_installed_plugins_commands(self, plugin_name=None):
        # TODO@geo investigate and see if we can make the plugin commands available in the interactive mode
        # after plugin was installed. Currently we need to exit the cli interactive mode to see the new commands
        if plugin_name:
            plugins = [self.get_plugin_by_name(plugin_name)]
        else:
            # load all plugins
            plugins = self.get_plugins()

        for plugin in plugins:
            plugin_name = plugin['id']
            if config.is_plugin_installed(plugin_name):
                for job_name in self.get_plugin_extra_jobs(plugin_name):
                    command_name = '{plugin_name} {job_name}'.format(plugin_name=plugin_name, job_name=job_name)
                    self.add_command(str(command_name), PluginCustomCommands, plugin_name)

                # here we can plugin custom commands for cluster
                if plugin['type'] in ['cluster']:
                    for cluster_cmd, cmd_cls in self.PLUGIN_CLUSTER_COMMANDS.items():
                        command_name = '{plugin_name} {cluster_cmd}'.format(plugin_name=plugin_name,
                                                                            cluster_cmd=cluster_cmd)

                        self.add_command(str(command_name), cmd_cls, plugin_name)

    def unload_removed_plugins_commands(self, plugin_name):
        plugins = [self.get_plugin_by_name(plugin_name)]

        for plugin in plugins:
            plugin_name = plugin['id']
            for job_name in self.get_plugin_extra_jobs(plugin_name):
                command_name = '{plugin_name} {job_name}'.format(plugin_name=plugin_name, job_name=job_name)
                self.remove_command(command_name, plugin_name)

    def remove_command(self, command_name, plugin_name):
        logger.debug("[%s] Unload plugin command: '%s'", plugin_name, command_name)
        self.command_manager.remove_command(command_name)

    def add_command(self, command_name, command_cls, plugin_name):
        logger.debug("[%s] Load plugin command: '%s'", plugin_name, command_name)
        # str(command_name) is required because cmd module gives error otherwise
        # when we are using from __future__ import unicode_literals
        self.command_manager.add_command(str(command_name), command_cls)
