from __future__ import print_function, unicode_literals

from madcore.cmds.configure import Configure
from madcore.logs import logging


class Registration(Configure):
    _description = "Register madcore"
    log = logging.getLogger(__name__)
