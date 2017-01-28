from __future__ import print_function, unicode_literals

import logging

from cliff.lister import Lister

from madcore import const
from madcore.configs import config
from madcore.libs.cloudformation import StackManagement


class Destroy(StackManagement, Lister):
    logger = logging.getLogger(__name__)
    _description = "Destroy madcore"

    def get_parser(self, prog_name):
        parser = super(Destroy, self).get_parser(prog_name)

        parser.add_argument('--force', default=False, action='store_true', dest='force',
                            help="Destroy without confirmation.")
        return parser

    def take_action(self, parsed_args):
        self.log_figlet("Destroy")
        if not parsed_args.force:
            self.ask_question_and_continue_on_yes("Are you sure you want to destroy?", start_with_yes=False)

        all_stacks = self.cf_client.describe_stacks()

        skip_remove_stack_names = [const.STACK_S3, const.STACK_DNS]

        deleted_stacks = []

        for stack_details in all_stacks['Stacks']:
            stack_name = stack_details['StackName']
            if stack_name not in skip_remove_stack_names:
                deleted_stacks.append(
                    (stack_name, self.delete_stack_if_exists(stack_name)))

        if not deleted_stacks:
            self.logger.info("Nothing to destroy.")

        config.delete_global_params()
        # remove all the data related to plugins
        config.delete_plugins(self.get_plugin_names())

        return (
            ('StackName', 'Deleted'),
            deleted_stacks
        )
