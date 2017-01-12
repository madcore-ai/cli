from __future__ import print_function, unicode_literals

from cliff.command import Command

from madcore.base import JenkinsBase
from madcore.logs import logging


class SelfTest(JenkinsBase, Command):
    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        job = 'madcore.selftest'
        self.jenkins_run_job_show_output(job)

        return 0
