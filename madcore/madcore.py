from __future__ import unicode_literals, print_function

import sys
import traceback

from cliff.app import App
from cliff.commandmanager import CommandManager

import utils
from base import Stdout
from cmds import configure
from cmds import create
from cmds import delete
from cmds import endpoints
from cmds import followme
from cmds import registration
from cmds import selftest
from cmds import stacks
from configs import config
from logs import logging


class MadcoreCli(App):
    def __init__(self):
        command = CommandManager('madcorecli.app')
        super(MadcoreCli, self).__init__(
            description='Madcore Core CLI - Deep Learning & Machine Intelligence Infrastructure Controller'
                        'Licensed under MIT (c) 2015-2017 Madcore Ltd - https://madcore.ai',
            version='0.3',
            command_manager=command,
            stdout=Stdout()
        )
        commands = {
            'configure': configure.Configure,
            'stacks': stacks.Stacks,
            'create': create.Create,
            'delete': delete.Delete,
            'followme': followme.Followme,
            'endpoints': endpoints.Endpoints,
            'selftest': selftest.SelfTest,
            'registration': registration.Registration
        }

        for k, v in commands.iteritems():
            command.add_command(k, v)

    def configure_logging(self):
        self.LOG = logging.getLogger('madcore')

    def trigger_configuration(self):
        # Trigger configure if not yet setup
        if not config.get_user_data():
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

        if not isinstance(cmd, configure.Configure):
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
