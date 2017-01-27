import argparse


class MadcoreException(Exception):
    pass


class ParameterValidationError(argparse.ArgumentTypeError):
    pass


class AutoScaleGroupNoActivities(MadcoreException):
    pass
