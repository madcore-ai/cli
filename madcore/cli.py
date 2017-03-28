from __future__ import unicode_literals, print_function

import logging
import sys
import traceback

from cliff.app import App
from cliff.commandmanager import CommandManager

from madcore import utils
from madcore.base import Stdout, PluginsBase
from madcore.cmds import configure
from madcore.cmds import destroy
from madcore.cmds import status
from madcore.configs import config
from madcore.libs.input_questions import Questionnaire
from madcore.libs.plugins_loader import PluginLoader


class MadcoreCommandManager(CommandManager):
    def __init__(self, namespace, convert_underscores=True):
        super(MadcoreCommandManager, self).__init__(namespace, convert_underscores)

    def remove_command(self, name):
        if name in self.commands:
            del self.commands[name]


class MadcoreCli(App):
    def __init__(self):
        command_manager = MadcoreCommandManager('madcorecli.app')
        super(MadcoreCli, self).__init__(
            description='Madcore Core CLI - Deep Learning & Machine Intelligence Infrastructure Controller'
                        'Licensed under MIT (c) 2015-2017 Madcore Ltd - https://madcore.ai',
            version='0.4',
            command_manager=command_manager,
            stdout=Stdout(),
            deferred_help=False
        )

        self.raw_cmd_args = None

        self.plugin_loader = PluginLoader(command_manager)
        self.reload_commands()

    def run_subcommand(self, argv):
        self.raw_cmd_args = argv
        return super(MadcoreCli, self).run_subcommand(argv)

    def load_extra_commands(self):
        # load other extra commands here
        commands = [
        ]

        for command_name, command_class in commands:
            self.command_manager.add_command(command_name, command_class)

    def reload_commands(self):
        self.plugin_loader.load_installed_plugins_commands()
        self.load_extra_commands()

    def build_option_parser(self, description, version,
                            argparse_kwargs=None):
        parser = super(MadcoreCli, self).build_option_parser(description, version, argparse_kwargs=argparse_kwargs)
        # we add here custom args

        return parser

    def configure_logging(self):
        self.LOG = logging.getLogger('madcore')

    def trigger_configuration(self):
        if not config.get_user_data() or not config.get_login_data():
            ask_msg = 'CLI must be configured to use this command. Do you want to begin?'
            start_config_selector = Questionnaire()
            start_config_selector.add_question('answer', options=['yes', 'no'], prompt=ask_msg)
            start_config = start_config_selector.run()

            if start_config['answer'] == 'yes':
                self.run_subcommand(['configure'])
            else:
                self.LOG.info("EXIT.")
                sys.exit(1)
        else:
            self.LOG.info("Already configured.")

    def initialize_app(self, argv):
        print()
        print()
        print("Madcore Core CLI - Deep Learning & Machine Intelligence Infrastructure Controller")
        print("v%s Licensed under MIT (c) 2015-2017 Madcore Ltd - https://madcore.ai" % utils.get_version())
        print()
        self.LOG.debug('initialize_app')
        # here we need to trigger
        if not argv:
            self.trigger_configuration()

    def prepare_to_run_command(self, cmd):
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)

        if not isinstance(cmd, (configure.Configure, destroy.Destroy, PluginsBase, status.Status)):
            self.trigger_configuration()

    def clean_up(self, cmd, result, err):
        # self.LOG.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.LOG.debug('Got an error: %s', err)
            self.LOG.debug(traceback.format_exc())


def main(argv=sys.argv[1:]):
    myapp = MadcoreCli()
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
