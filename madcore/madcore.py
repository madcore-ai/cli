from __future__ import unicode_literals, print_function

import os
import sys

from cliff import complete
from cliff.app import App
from cliff.commandmanager import CommandManager

import configure
import core
import stack
import utils


class MadcoreCli(App):
    def __init__(self):
        command = CommandManager('madcorecli.app')
        super(MadcoreCli, self).__init__(
            description='Madcore Core CLI - Deep Learning & Machine Intelligence Infrastructure Controller'
                        'Licensed under MIT (c) 2015-2017 Madcore Ltd - https://madcore.ai',
            version='0.2',
            command_manager=command,
        )
        commands = {
            'complete': complete.CompleteCommand,
            'configure': configure.Configure,
            'stack list': stack.StackList,
            'stack create': stack.StackCreate,
            'stack delete': stack.StackDelete,
            'core followme': core.CoreFollowme,
        }

        for k, v in commands.iteritems():
            command.add_command(k, v)

    def initialize_app(self, argv):
        print()
        print()
        print("Madcore Core CLI - Deep Learning & Machine Intelligence Infrastructure Controller")
        print()
        print("Licensed under MIT (c) 2015-2017 Madcore Ltd - https://madcore.ai")
        print()
        self.LOG.debug('initialize_app')

    def prepare_to_run_command(self, cmd):
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)

        # TODO@geo we need to find a better way for this
        # Trigger configure if not yet setup
        if not os.path.exists(os.path.join(utils.config_path(), 'cloudformation')):
            os.system('madcore configure')

    def clean_up(self, cmd, result, err):
        self.LOG.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.LOG.debug('got an error: %s', err)


def main(argv=sys.argv[1:]):
    myapp = MadcoreCli()
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
