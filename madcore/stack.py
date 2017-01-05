import os
import sys
import logging
import boto3
import prettytable
import argparse
from cliff.app import App
from cliff.commandmanager import CommandManager
from cliff.command import Command
from cliff.show import ShowOne
from cliff.lister import Lister

class StackDescribe(Lister):
    """Show a list of files in the current directory.

    The file name and size are printed by default.
    """

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info('STACK DESCRIBE info')
        self.log.debug('STACK DESCRIBE debugging')
        self.app.stdout.write('STACK DESCRIBE STDOUT\n')
        cf = boto3.resource('cloudformation')
        return (('Name', 'Status','Creation Time','Last Updated Time'),
                ([(stack.name,stack.stack_status,stack.creation_time,stack.last_updated_time) for stack in cf.stacks.all()])
                )

class Stack(Command):
    "Show details about a file"

    log = logging.getLogger(__name__)

    def stack_list(self, *args):
        self.app.stdout.write('STACK LISTING...\n')

    def stack_describe(self, *args):
        self.app.stdout.write('STACK DESCRIBING...\n')

    def stack_create(self, *args):
        self.app.stdout.write('STACK CREATING...\n')

    def get_parser(self, prog_name):
        parser = super(Stack, self).get_parser(prog_name)
        sp = parser.add_subparsers()
        sp_list = sp.add_parser('list', help='Starts %(prog)s daemon')
        sp_describe = sp.add_parser('describe', help='Starts %(prog)s daemon')
        sp_create = sp.add_parser('create', help='Starts %(prog)s daemon')
        #group = parser.add_mutually_exclusive_group()
        #parser.add_argument('list', nargs='?', default='.')
        #parser.add_argument('create', nargs='*', default='.')
        parser.add_argument('args', nargs=1) #or nargs=argparse.REMAINDER for multi args

        sp_create.set_defaults(func=self.stack_create)
        sp_list.set_defaults(func=self.stack_list)
        sp_describe.set_defaults(func=self.stack_describe)
        return parser

    def take_action(self, parsed_args):
        self.log.info('STACK TAKE ACTION info')
        self.log.debug('STACK TAKE ACTION debugging')
        self.app.stdout.write('STACK TAKE ACTION STDOUT\n')
        parsed_args.func(parsed_args)


class Error(Command):
    "Always raises an error"

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.info('causing error')
        raise RuntimeError('this is the expected exception')


