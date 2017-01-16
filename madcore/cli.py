from __future__ import unicode_literals, print_function

import logging
import sys
import traceback

from cliff.app import App
from cliff.commandmanager import CommandManager

from madcore import utils
from madcore.base import Stdout
from madcore.cmds import configure
from madcore.cmds import create
from madcore.cmds import destroy
from madcore.cmds import endpoints
from madcore.cmds import followme
from madcore.cmds import registration
from madcore.cmds import selftest
from madcore.cmds import stacks
from madcore.configs import config


class MadcoreCli(App):
    def __init__(self):
        command_manager = CommandManager('madcorecli.app')
        super(MadcoreCli, self).__init__(
            description='Madcore Core CLI - Deep Learning & Machine Intelligence Infrastructure Controller'
                        'Licensed under MIT (c) 2015-2017 Madcore Ltd - https://madcore.ai',
            version='0.3',
            command_manager=command_manager,
            stdout=Stdout()
        )
        commands = {
            'configure': configure.Configure,
            'stacks': stacks.Stacks,
            'create': create.Create,
            'destroy': destroy.Destroy,
            'followme': followme.Followme,
            'endpoints': endpoints.Endpoints,
            'selftest': selftest.SelfTest,
            'registration': registration.Registration
        }

        for command_name, command_class in commands.iteritems():
            command_manager.add_command(command_name, command_class)

    def configure_logging(self):
        self.LOG = logging.getLogger('madcore')

    def trigger_configuration(self):
        # Trigger configure if not yet setup
        if config.is_config_deleted or not config.get_user_data():
            self.run_subcommand(['configure'])
        else:
            self.LOG.info("Already configured.")

    def initialize_app(self, argv):
        print()
        print()
        print("Madcore Core CLI - Deep Learning & Machine Intelligence Infrastructure Controller")
        print(utils.get_version())
        print("Licensed under MIT (c) 2015-2017 Madcore Ltd - https://madcore.ai")
        print()
        self.LOG.debug('initialize_app')
        # here we need to trigger
        if not argv:
            self.trigger_configuration()

    def prepare_to_run_command(self, cmd):
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)

        if not isinstance(cmd, (configure.Configure, destroy.Destroy)):
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
