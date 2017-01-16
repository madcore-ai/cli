from __future__ import print_function, unicode_literals

import logging

from madcore.cmds.configure import Configure


class Create(Configure):
    _description = "Create madcore"
    logger = logging.getLogger(__name__)
