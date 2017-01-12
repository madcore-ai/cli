from __future__ import print_function, unicode_literals

import os
import ssl

from cliff.lister import Lister

from madcore.base import JenkinsBase
from madcore.configs import config
from madcore.configure import MadcoreConfigure
from madcore.const import DOMAIN_REGISTRATION
from madcore.logs import logging


class Registration(JenkinsBase, Lister):
    _description = "Register madcore"
    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        configure = MadcoreConfigure()
        config_results = configure.start_configuration()
        # TODO@geo move this functionality to a class and call from there
        os.system('madcore create')

        # TODO#geo this is a hack to skip ssl verification
        ssl._create_default_https_context = ssl._create_unverified_context

        job = 'madcore.registration'
        parameters = DOMAIN_REGISTRATION.copy()
        parameters['Hostname'] = config.get_user_data('user_domain')
        parameters['Email'] = config.get_user_data('email')

        self.jenkins_run_job_show_output(job, parameters=parameters)

        # TODO@geo call this from code not cmd line
        os.system('madcore selftest')

        return config_results
