from picoparse import any_token
from picoparse import fail
from picoparse import one_of
from picoparse import optional
from picoparse import remaining
from picoparse.text import whitespace
from picoparse.text import caseless_string

from ..models import Form
from ..pico import wrap as pico
from ..router import FormatError

class Echo(Form):
    @pico
    def parse(cls):
        one_of('+')
        caseless_string('echo')
        whitespace()

        return {
            'echo': "".join(remaining())
            }

    def handle(self, echo=None):
        self.reply(echo)

class Empty(Form):
    @pico
    def parse(cls):
        if optional(any_token, None):
            fail()

    def handle(self):
        self.reply(u"You sent a message with no text.")

class Error(Form):
    @pico
    def parse(cls):
        one_of('+')
        caseless_string('error')
        raise FormatError("error")

class Broken(Form):
    @pico
    def parse(cls):
        one_of('+')
        caseless_string('break')

    def __init__(self, *args, **kwargs):
        raise RuntimeError("Broken")

class BadConfiguration(Form):
    @pico
    def parse(cls):
        one_of('+')
        caseless_string('bad')
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("".join(remaining()))

class Hello(Form):
    @pico
    def parse(cls):
        one_of('+')
        caseless_string('hello')

    def handle(self):
        pass
