from __future__ import print_function, unicode_literals

import logging
import os

from cliff.command import Command

from madcore.configs import config
from madcore.const import STACK_CORE
from madcore.libs.cloudformation import StackManagement


class MadcoreSSH(StackManagement, Command):
    _description = "SSH to madcore instance"

    logger = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        core_stack_details = self.get_stack(STACK_CORE)

        if core_stack_details is None:
            self.logger.info("Madcore not created yet, run configuration to setup.")
            self.exit()

        core_public_ip = self.get_output_from_dict(core_stack_details['Outputs'], 'MadCorePublicIp')
        ssh_cmd = 'ssh ubuntu@{public_ip} -i {ssh_priv_file}'.format(public_ip=core_public_ip,
                                                                     ssh_priv_file=config.get_aws_data(
                                                                         'ssh_priv_file'))
        self.logger.info(ssh_cmd)
        os.system(ssh_cmd)

        return 0
