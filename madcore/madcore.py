import os
import sys
import logging
from cliff.app import App
from cliff.commandmanager import CommandManager
from cliff.command import Command
from cliff.show import ShowOne
from cliff.lister import Lister
import stack


class MadcoreCli(App):

    def __init__(self):
        command = CommandManager('madcorecli.app')
        super(MadcoreCli, self).__init__(
                description='sample app',
                version='0.1',
                command_manager=command,
        )
        commands = {
            'stack': stack.Stack,
        }

        for k, v in commands.iteritems():
            command.add_command(k, v)

    def initialize_app(self, argv):
        self.LOG.debug('initialize_app')

    def prepare_to_run_command(self, cmd):
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)

    def clean_up(self, cmd, result, err):
        self.LOG.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.LOG.debug('got an error: %s', err)


def main(argv=sys.argv[1:]):
    myapp = MadcoreCli()
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
