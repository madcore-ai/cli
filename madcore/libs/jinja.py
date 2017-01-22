from __future__ import unicode_literals, print_function

from jinja2 import Environment
from jinja2.defaults import VARIABLE_START_STRING

ENV = Environment()


def jinja_render_string(input_val, check_input=True, **kwargs):
    if not isinstance(input_val, basestring):
        return input_val

    # TODO@geo find a better way to check if string is a jinja format
    if check_input and VARIABLE_START_STRING not in input_val:
        return input_val

    return ENV.from_string(input_val).render(**kwargs)
