from __future__ import unicode_literals, print_function

import jenkins
from jenkins import Request, JenkinsException, HTTPError, NotFoundException, urlopen

PROGRESSIVE_TEXT_OUTPUT = '%(folder_url)sjob/%(short_name)s/%(number)d/logText/progressiveText?start=%(start)s'


# TODO@geo
# Currently https://github.com/openstack/python-jenkins does not have this implemented
# maybe we should make a PR?

class JenkinsServer(jenkins.Jenkins):
    def progressive_text(self, name, number, start):
        folder_url, short_name = self._get_job_folder(name)

        try:
            req = Request(self._build_url(PROGRESSIVE_TEXT_OUTPUT, locals()))

            response = urlopen(req, timeout=self.timeout)

            response_info = response.info()

            new_start = response_info.getheaders('X-Text-Size')
            if new_start:
                new_start = new_start[0]

            has_more_data = bool(response_info.getheaders('X-More-Data'))

            text = response.read()

            return new_start, has_more_data, text

        except HTTPError as e:
            raise JenkinsException('Error while reading job[%s] number[%d]' % (name, number))
        except NotFoundException:
            raise JenkinsException('job[%s] number[%d] does not exist'
                                   % (name, number))
