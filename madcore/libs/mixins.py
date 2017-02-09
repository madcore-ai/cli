from __future__ import unicode_literals, print_function

from cliff.command import Command


class BasePluginCommand(Command):
    def get_parser(self, prog_name):
        parser = super(BasePluginCommand, self).get_parser(prog_name)

        parser.add_argument('-sc', '--skip-confirm-default-params', default=False, action='store_true',
                            dest='skip_confirm_default_params',
                            help='Ask for plugin input params confirmation')
        parser.add_argument('-rp', '--reset-params', default=False, action='store_true',
                            dest='reset_params',
                            help="Reset previously stored params")
        parser.add_argument('-f', '--force', default=False, action='store_true',
                            dest='force',
                            help="Ignore previous states and rerun the command.")
        return parser

    @classmethod
    def add_params_to_arg_parser(cls, parser, params):
        # Here we save all the user input params with '_' prefix to not get conflicted with the cli defined ones
        for job_param in params:
            arg_params = {
                'dest': '_%s' % job_param['name'],
                'type': job_param['validator'],
                'help': job_param['description']
            }
            if 'allowed' in job_param:
                arg_params['choices'] = job_param['allowed']

            parser.add_argument(
                '--%s' % job_param['name'],
                **arg_params
            )

        return parser

    def get_raw_cmd_args(self):
        # at this stage we don't have the plugin name we want to install
        # so, we are using some hack to get it
        raw_cmd_args = self.app.raw_cmd_args[:]

        if raw_cmd_args[0] == 'help':
            del raw_cmd_args[0]

        return raw_cmd_args

    def get_plugin_name_from_input_args(self):
        plugin_name = None

        try:
            raw_cmd_args = self.get_raw_cmd_args()
            subcommand = self.app.command_manager.find_command(raw_cmd_args)
            _, _, sub_argv = subcommand
            plugin_name = sub_argv[0]
        except Exception:
            pass

        return plugin_name


class PluginCommand(BasePluginCommand):
    def get_parser(self, prog_name):
        parser = super(PluginCommand, self).get_parser(prog_name)

        parser.add_argument('plugin_name', choices=self.get_plugin_names(), help='Input plugin name')
        return parser
