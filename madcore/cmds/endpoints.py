from __future__ import print_function, unicode_literals

from cliff.lister import Lister

from madcore.base import MadcoreBase
from madcore.const import ENDPOINTS


class Endpoints(MadcoreBase, Lister):
    def take_action(self, parsed_args):
        data = []

        for endpoint in ENDPOINTS:
            self.get_endpoint_url(endpoint)
            data.append((endpoint, self.get_endpoint_url(endpoint)))

        return (
            ('Endpoint', 'Url'),
            data
        )
