import logging

from cliff.lister import Lister

from madcore.base import PluginsBase

logger = logging.getLogger(__name__)


class PluginList(PluginsBase, Lister):
    def take_action(self, parsed_args):
        # TODO@geo use logger to log info
        logger.info("Plugin list")

        plugins = self.get_json_from_url(
            'https://raw.githubusercontent.com/madcore-ai/plugins/master/plugins-index.json')

        data = []

        for plugin in plugins['products']:
            data.append((
                plugin['id'],
                plugin['type'],
                plugin['description'],
            ))

        return (
            ('Id', 'Type', 'description'),
            data
        )
