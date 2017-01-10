from __future__ import print_function, unicode_literals

import logging
import ssl

from cliff.command import Command

from base import JenkinsBase


class CoreSelfTest(JenkinsBase, Command):
    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        # TODO#geo this is a hack to skip ssl verification
        ssl._create_default_https_context = ssl._create_unverified_context
        job = 'madcore.selftest'
        self.jenkins_run_job_show_output(job)

        return 0
