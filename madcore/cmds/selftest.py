from __future__ import print_function, unicode_literals

import logging

from madcore.libs.jenkins import JenkinsJobCommand


class SelfTest(JenkinsJobCommand):
    _description = "Run jenkins selftests"
    logger = logging.getLogger(__name__)
    job_name = 'madcore.selftest'
