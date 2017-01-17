import logging

from cliff.lister import Lister

from madcore.base import PluginsBase

logger = logging.getLogger(__name__)


class PluginList(PluginsBase, Lister):
    def take_action(self, parsed_args):
        logger.info("Plugin list")

        data = []

        for plugin in self.get_plugins():
            data.append((
                plugin['id'],
                plugin['type'],
                plugin['description'],
            ))

        return (
            ('Id', 'Type', 'description'),
            data
        )
