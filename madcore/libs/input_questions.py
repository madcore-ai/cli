from __future__ import unicode_literals, print_function

import sys

import questionnaire
from questionnaire.prompters import register


@register(key="raw")
def raw(prompt="", **kwargs):
    """Calls input to allow user to input an arbitrary string. User can go
    back by entering the `go_back` string. Works in both Python 2 and 3.
    """
    go_back = kwargs["go_back"] if "go_back" in kwargs else "<"
    type_ = kwargs["type"] if "type" in kwargs else str
    default_value = kwargs.get('default', None)

    while True:
        try:
            answer = eval('raw_input(prompt)') if sys.version_info < (3, 0) \
                else eval('input(prompt)')
            if not answer and default_value is not None:
                answer = default_value

            return (answer, 1) if answer == go_back else (type_(answer), None)
        except ValueError:
            print("\n`{}` is not a valid `{}`\n".format(answer, type_))


class Questionnaire(questionnaire.Questionnaire):
    default_values = {}

    def add_question(self, *args, **kwargs):
        question = questionnaire.Questionnaire.add_question(self, *args, **kwargs)
        if 'default' in kwargs:
            key = args[0]
            self.default_values[key] = kwargs['default']

        return question

    def ask_question(self, q):
        """Call the question's prompter, and check to see if user goes back.
        """
        prompt = q.prompt
        if self._show_answers:
            new_prompt = q.prompt
            if q.key in self.default_values:
                new_prompt = "{}[{}] ".format(q.prompt, self.default_values[q.key])
            prompt = self.show_answers() + "\n{}".format(new_prompt)

        answer, back = q.prompter(prompt, **q.prompter_args)
        if not answer and q.key in self.default_values:
            answer = self.default_values[q.key]
        self.answers[q.key] = answer
        if back is not None:
            self.go_back(abs(int(back)))
            return False
        return True
