from __future__ import print_function, unicode_literals

import logging

from cliff.lister import Lister

from madcore.base import PluginsBase
from madcore.configs import config

logger = logging.getLogger(__name__)


class PluginList(PluginsBase, Lister):
    _description = "List madcore plugins"

    def take_action(self, parsed_args):
        logger.info("Plugin list")

        data = []

        for plugin in self.get_plugins():
            data.append((
                plugin['id'],
                plugin['description'],
                config.is_plugin_installed(plugin['id'])
            ))

        return (
            ('Name', 'Description', 'Installed'),
            data
        )
