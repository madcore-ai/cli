from __future__ import unicode_literals, print_function

import sys

import questionnaire
from questionnaire.prompters import register

from madcore.exceptions import ParameterValidationError
from madcore.libs.jinja import jinja_render_string


@register(key="raw")
def raw(prompt="", **kwargs):
    """Calls input to allow user to input an arbitrary string. User can go
    back by entering the `go_back` string. Works in both Python 2 and 3.
    """
    go_back = kwargs["go_back"] if "go_back" in kwargs else "<"
    type_ = kwargs["type"] if "type" in kwargs else str
    jinja_params = kwargs.get('jinja_params', {})
    default_value = kwargs.get('default', None)

    while True:
        try:
            answer = eval('raw_input(prompt)') if sys.version_info < (3, 0) \
                else eval('input(prompt)')
            if not answer and default_value is not None:
                answer = jinja_render_string(default_value, **jinja_params)

            return (answer, 1) if answer == go_back else (type_(answer), None)
        except ParameterValidationError as validation_error:
            print("\n{}\n".format(validation_error))


class Questionnaire(questionnaire.Questionnaire):
    DEFAULT_VALUE = 'default'
    DEFAULT_VALUE_LABEL = 'default_label'
    default_values = {}
    default_values_label = {}

    def __init__(self, madcore_jinja_params=None, show_answers=True):
        if madcore_jinja_params is not None:
            self.madcore_jinja_params = madcore_jinja_params.copy()
        else:
            self.madcore_jinja_params = {}
        questionnaire.Questionnaire.__init__(self, show_answers=show_answers)

    @property
    def jinja_params(self):
        self.madcore_jinja_params.update(self.answers)
        return self.madcore_jinja_params

    def add_question(self, *args, **kwargs):
        question = questionnaire.Questionnaire.add_question(self, *args, **kwargs)

        key = args[0]
        if self.DEFAULT_VALUE in kwargs:
            self.default_values[key] = kwargs[self.DEFAULT_VALUE]
            # set by default label to value
            self.default_values_label[key] = kwargs[self.DEFAULT_VALUE]

        if kwargs.get(self.DEFAULT_VALUE_LABEL, None) is not None:
            self.default_values_label[key] = kwargs[self.DEFAULT_VALUE_LABEL]

        return question

    def ask_question(self, q):
        """Call the question's prompter, and check to see if user goes back.
        """
        prompt = q.prompt
        if self._show_answers:
            new_prompt = prompt
            if q.key in self.default_values:
                # there are cases when we want to set different label for default value
                # if label no set as input, use default input value
                default_values_label = self.default_values_label.get(q.key, self.default_values[q.key])
                default_values_label = jinja_render_string(default_values_label, **self.jinja_params)
                new_prompt = "{}[{}] ".format(q.prompt, default_values_label)
            prompt = self.show_answers() + "\n{}".format(new_prompt)

        answer, back = q.prompter(prompt, jinja_params=self.jinja_params, **q.prompter_args)

        # read the answer from default values if not set by user and exists in defaults
        # update default value with the final answer result
        if answer and q.key in self.default_values:
            self.default_values[q.key] = answer

        self.answers[q.key] = answer
        if back is not None:
            self.go_back(abs(int(back)))
            return False
        return True
