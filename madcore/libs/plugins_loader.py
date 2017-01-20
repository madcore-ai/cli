from __future__ import unicode_literals, print_function

import logging

from madcore.base import PluginsBase
from madcore.cmds.plugins.cluster import PluginClusterExtendBy, PluginClusterContractBy, PluginClusterZero
from madcore.cmds.plugins.commands import PluginCustomCommands
from madcore.configs import config

logger = logging.getLogger(__name__)


class PluginLoader(PluginsBase):
    PLUGIN_CLUSTER_COMMANDS = {
        'extend': PluginClusterExtendBy,
        'contract': PluginClusterContractBy,
        'zero': PluginClusterZero,
    }

    def __init__(self, command_manager):
        self.command_manager = command_manager

    def load_installed_plugins_commands(self):
        # TODO@geo investigate and see if we can make the plugin commands available in the interactive mode
        # after plugin was installed. Currently we need to exit the cli interactive mode to see the new commands
        for plugin in self.get_plugins():
            plugin_name = plugin['id']
            if config.is_plugin_installed(plugin_name):
                for job_name in self.get_plugin_extra_jobs(plugin_name):
                    command_name = '{plugin_name} {job_name}'.format(plugin_name=plugin_name, job_name=job_name)
                    self.add_command(str(command_name), PluginCustomCommands)

                if plugin['type'] in ['cluster']:
                    for cluster_cmd, cmd_cls in self.PLUGIN_CLUSTER_COMMANDS.items():
                        command_name = '{plugin_name} {cluster_cmd}'.format(plugin_name=plugin_name,
                                                                            cluster_cmd=cluster_cmd)

                        self.add_command(str(command_name), cmd_cls)

    def add_command(self, command_name, command_cls):
        logger.debug("Load plugin command: '%s'" % command_name)
        # str(command_name) is required because cmd module gives error otherwise
        # when we are using from __future__ import unicode_literals
        self.command_manager.add_command(str(command_name), command_cls)
