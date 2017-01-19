from __future__ import print_function, unicode_literals

import logging

from cliff.show import ShowOne

from madcore.const import STACK_CORE
from madcore.libs.cloudformation import StackManagement


class MadcoreUp(StackManagement, ShowOne):
    _description = "Start madcore instance"

    logger = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        core_stack_details = self.get_stack(STACK_CORE)

        if core_stack_details is None:
            self.logger.info("Madcore not created yet, run configuration to setup.")
            self.exit()

        core_instance_id = self.get_output_from_dict(core_stack_details['Outputs'], 'MadCoreInstanceId')
        instance_running = self.start_instance_if_not_running(core_instance_id, '[MADCORE-UP] ')

        if instance_running:
            self.logger.info("OK.")
        columns = (
            'State',
        )
        data = (
            'OK' if instance_running else 'NOT OK',
        )
        return columns, data
