from __future__ import unicode_literals, print_function

from madcore.exceptions import ParameterValidationError


class BaseValidator(object):
    def validate(self, val):
        raise NotImplementedError

    def __call__(self, val, **kwargs):
        return self.validate(val)

    def _raise_error(self, val):
        raise ParameterValidationError("'%s' has invalid type, should be '%s'" % (val, self))


class BoolValidator(BaseValidator):
    allowed_values_true = [True, 'yes', 'true', 'TRUE', 'True', '1']
    allowed_values_false = [None, False, 'no', 'false', 'FALSE', 'False', '0', '']

    def __str__(self):
        return "boolean"

    def validate(self, val):
        if val in self.allowed_values_true:
            return True
        elif val in self.allowed_values_false:
            return False
        else:
            self._raise_error(val)


class StringValidator(BaseValidator):
    def __str__(self):
        return "string"

    def validate(self, val):
        try:
            return str(val)
        except Exception:
            self._raise_error(val)


class IntegerValidator(BaseValidator):
    def __str__(self):
        return "integer"

    def validate(self, val):
        try:
            return int(val)
        except Exception:
            self._raise_error(val)


class IntegerPositiveValidator(BaseValidator):
    def __str__(self):
        return "integer_positive"

    def validate(self, val):
        try:
            val = int(val)
            if val < 0:
                raise
            return val
        except Exception:
            self._raise_error(val)


class IntegerGtZeroValidator(BaseValidator):
    def __str__(self):
        return "integer_greater_then_zero"

    def validate(self, val):
        try:
            val = int(val)
            if val <= 0:
                raise
            return val
        except Exception:
            self._raise_error(val)


# Any other validators to be added here
VALIDATORS = {
    'bool': BoolValidator(),
    'string': StringValidator(),
    'integer': IntegerValidator(),
    'integer_gt_zero': IntegerGtZeroValidator(),
    'integer_positive': IntegerPositiveValidator()
}


def get_validator(param_type):
    return VALIDATORS.get(param_type, StringValidator)
