from __future__ import print_function, unicode_literals

import logging
import ssl

from cliff.command import Command

from base import JenkinsBase
from const import DOMAIN_REGISTRATION


class CoreRegistration(JenkinsBase, Command):
    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        # TODO#geo this is a hack to skip ssl verification
        ssl._create_default_https_context = ssl._create_unverified_context

        job = 'madcore.registration'
        domain_name, sub_domain_name = self.get_dns_domains()

        parameters = DOMAIN_REGISTRATION.copy()
        parameters['Hostname'] = '{}.{}'.format(sub_domain_name, domain_name)

        self.jenkins_run_job_show_output(job, parameters=parameters)

        return 0
