from __future__ import print_function, unicode_literals

import logging

from cliff.command import Command

from madcore.base import JenkinsBase


class JenkinsJobCommand(JenkinsBase, Command):
    logger = logging.getLogger(__name__)
    job_name = None

    def take_action(self, parsed_args):
        if self.job_name is None:
            self.logger.error("You need to define a job_name.")
            self.exit()
        self.jenkins_run_job_show_output(self.job_name)

        return 0
