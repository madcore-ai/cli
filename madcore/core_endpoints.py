from __future__ import print_function, unicode_literals

from cliff.lister import Lister

from base import CloudFormationBase
from const import ENDPOINTS


class CoreEndpoints(CloudFormationBase, Lister):
    def take_action(self, parsed_args):
        domain_name, sub_domain_name = self.get_dns_domains()

        data = []

        for endpoint in ENDPOINTS.keys():
            data.append((endpoint, 'https://{}.{}.{}'.format(endpoint, sub_domain_name, domain_name)))

        return (
            ('Endpoint', 'Url'),
            data
        )
