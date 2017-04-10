from __future__ import print_function, unicode_literals

import logging

from madcore.configs import config
from madcore.const import PLUGIN_NAME_INGRESS
from madcore.libs.mixins import PluginCommand
from madcore.libs.plugins import PluginManagement

logger = logging.getLogger(__name__)


class PluginInstall(PluginManagement, PluginCommand):
    _description = "Install madcore plugins"
    plugin_job = 'deploy'
    _plugin_name = None

    @property
    def plugin_name(self):
        if not self._plugin_name:
            self._plugin_name = self.get_plugin_name_from_input_args()
        return self._plugin_name

    def get_parser(self, prog_name):
        parser = super(PluginInstall, self).get_parser(prog_name)

        if self.plugin_name in self.get_plugin_names():
            params = self.get_plugin_job_all_params(self.plugin_name, self.plugin_job)
            parser = self.add_params_to_arg_parser(parser, params)

        if self.plugin_name not in (PLUGIN_NAME_INGRESS, ):
            parser.add_argument('--ingress', default=False, action='store_true',
                                dest='ingress_flag',
                                help="Set to install plugin as ingress.")
        return parser

    @classmethod
    def should_install_ingress_plugin(cls, parsed_args):
        ingress_flag = getattr(parsed_args, 'ingress_flag', None)
        if ingress_flag and not config.is_plugin_installed(PLUGIN_NAME_INGRESS):
            return True

        return False

    def take_action(self, parsed_args):
        plugin_name = parsed_args.plugin_name

        if not parsed_args.force and config.is_plugin_installed(plugin_name):
            self.logger.info("[%s] Plugin already installed.", plugin_name)
            return 0
        elif self.should_install_ingress_plugin(parsed_args):
            self.logger.info("[%s] You need to install ingress plugin first when using "
                             "'--ingress' option.", plugin_name)
            return 0

        plugin_installed = self.execute_plugin_job(plugin_name, self.plugin_job, parsed_args)
        config.set_plugin_installed(plugin_name, plugin_installed)

        if parsed_args.force or plugin_installed:
            self.app.plugin_cmd_loader.load_installed_plugins_commands(plugin_name)
            self.logger.info("[%s] Successfully installed plugin.", plugin_name)
        else:
            self.logger.error("[%s] Error installing plugin.", plugin_name)

        return 0
