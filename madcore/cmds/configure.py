from __future__ import print_function, unicode_literals

import logging
import ssl

from cliff.lister import Lister

from madcore.base import JenkinsBase
from madcore.configs import config
from madcore.configure import MadcoreConfigure
from madcore.const import DOMAIN_REGISTRATION
from madcore.libs.cloudformation import StackCreate


class Configure(JenkinsBase, Lister):
    _description = "Configure madcore"
    logger = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        # TODO#geo this is a hack to skip ssl verification when we do jenkins registration
        ssl._create_default_https_context = ssl._create_unverified_context

        configure = MadcoreConfigure(self.app, self.app_args)
        config_results = configure.take_action(parsed_args)

        self.log_figlet("Cloudformation")
        stack_create = StackCreate(self.app, self.app_args)
        stack_create.take_action(parsed_args)

        self.log_figlet("Wait until Jenkins is up")
        if self.wait_until_jenkins_is_up():
            self.logger.info("Jenkins is up, continue.")
        else:
            self.logger.error("Error while waiting for jenkins.")
            self.exit()

        self.log_figlet("Start domain registration")
        self.logger.info("Check if domain is certificated...")
        is_domain_certified = self.wait_until_domain_is_certified()
        self.logger.info("Domain certificate found: %s", is_domain_certified)

        if is_domain_certified:
            config.set_user_data({"registration": True})
            self.logger.info("Domain already registered.")
        else:
            self.logger.info("Start domain registration.")

            job_name = 'madcore.registration'
            parameters = DOMAIN_REGISTRATION.copy()
            parameters['Hostname'] = config.get_full_domain()
            parameters['Email'] = config.get_user_data('email')

            success = self.jenkins_run_job_show_output(job_name, parameters=parameters)

            if success:
                self.logger.info("Successfully run job '%s'.", job_name)
                config.set_user_data({"registration": True})
            else:
                self.logger.error("Error while executing job '%s'.", job_name)
                config.set_user_data({"registration": False})

        # enable ssl and run the rest of jenkins jobs via ssl
        ssl._create_default_https_context = ssl.create_default_context
        self.log_figlet("Run selftests")
        self.app.run_subcommand(['selftest'])

        return config_results
