from __future__ import unicode_literals, print_function


class BaseValidator(object):
    def validate(self, val):
        raise NotImplementedError

    def __call__(self, val, **kwargs):
        return self.validate(val)


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
            raise ValueError


class StringValidator(BaseValidator):
    def __str__(self):
        return "string"

    def validate(self, val):
        return str(val)


class IntegerValidator(BaseValidator):
    def __str__(self):
        return "integer"

    def validate(self, val):
        return int(val)


# Any other validators to be added here
VALIDATORS = {
    'bool': BoolValidator(),
    'string': StringValidator(),
    'integer': IntegerValidator()
}


def get_validator(param_type):
    return VALIDATORS.get(param_type, StringValidator)
