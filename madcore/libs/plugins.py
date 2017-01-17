from cliff.command import Command


class PluginCommand(Command):
    def get_parser(self, prog_name):
        parser = super(PluginCommand, self).get_parser(prog_name)

        parser.add_argument('plugin_name', choices=self.get_plugin_names(), help='Input plugin name')
        return parser
