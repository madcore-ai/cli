

import logging

from cliff.command import Command


class Core(Command):
    "A simple command that prints a message."

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(File, self).get_parser(prog_name)
        parser.add_argument('stack', nargs='?', default='.')
        return parser

    def take_action(self, parsed_args):
        self.log.info('sending greeting')
        self.log.debug('debugging')
        self.app.stdout.write('hi!\n')


class Error(Command):
    "Always raises an error"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info('causing error')
        raise RuntimeError('this is the expected exception')