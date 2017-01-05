import os
import sys
import logging
import argparse
from cliff.app import App
from cliff.commandmanager import CommandManager
from cliff.command import Command
from cliff.show import ShowOne
from cliff.lister import Lister


class Stack(Command):
    "Show details about a file"

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Stack, self).get_parser(prog_name)
        parser.add_argument('list', nargs='?', default='.')
        parser.add_argument('args', nargs=1) #or nargs=argparse.REMAINDER for multi args
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


