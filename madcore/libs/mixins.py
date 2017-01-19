from __future__ import unicode_literals, print_function

from cliff.command import Command


class BasePluginCommand(Command):
    def get_parser(self, prog_name):
        parser = super(BasePluginCommand, self).get_parser(prog_name)

        parser.add_argument('-c', '--confirm-default-params', default=True, action='store_true',
                            dest='confirm_default_params',
                            help='Ask for plugin input params confirmation')
        parser.add_argument('-r', '--reset-params', default=False, action='store_true',
                            dest='reset_params',
                            help="Reset previously stored params")
        parser.add_argument('-f', '--force', default=False, action='store_true',
                            dest='force',
                            help="Ignore previous states and rerun the command.")
        return parser


class PluginCommand(BasePluginCommand):
    def get_parser(self, prog_name):
        parser = super(PluginCommand, self).get_parser(prog_name)

        parser.add_argument('plugin_name', choices=self.get_plugin_names(), help='Input plugin name')
        return parser
