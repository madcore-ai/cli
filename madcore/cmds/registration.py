from __future__ import print_function, unicode_literals

import logging

from madcore.cmds.configure import Configure


class Registration(Configure):
    _description = "Register madcore"
    logger = logging.getLogger(__name__)
