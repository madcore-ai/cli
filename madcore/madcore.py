from __future__ import unicode_literals, print_function

import os
import sys

from cliff import complete
from cliff.app import App
from cliff.commandmanager import CommandManager

import configure
import core_followme
import core_endpoints
import core_selftest
import stack_list
import stack_create
import stack_delete
import utils


class MadcoreCli(App):
    def __init__(self):
        command = CommandManager('madcorecli.app')
        super(MadcoreCli, self).__init__(
            description='Madcore Core CLI - Deep Learning & Machine Intelligence Infrastructure Controller'
                        'Licensed under MIT (c) 2015-2017 Madcore Ltd - https://madcore.ai',
            version='0.3',
            command_manager=command,
        )
        commands = {
            'complete': complete.CompleteCommand,
            'configure': configure.Configure,
            'stack list': stack_list.StackList,
            'stack create': stack_create.StackCreate,
            'stack delete': stack_delete.StackDelete,
            'core followme': core_followme.CoreFollowme,
            'core endpoints': core_endpoints.CoreEndpoints,
            'core selftest': core_selftest.CoreSelfTest
        }

        for k, v in commands.iteritems():
            command.add_command(k, v)

    def initialize_app(self, argv):
        print()
        print()
        print("Madcore Core CLI - Deep Learning & Machine Intelligence Infrastructure Controller")
        print("Licensed under MIT (c) 2015-2017 Madcore Ltd - https://madcore.ai")
        print()
        self.LOG.debug('initialize_app')

    def prepare_to_run_command(self, cmd):
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)

        if isinstance(cmd, configure.Configure):
            # no need to run configure when we configure
            return
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
