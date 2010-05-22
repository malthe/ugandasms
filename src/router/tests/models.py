from picoparse import any_token
from picoparse import fail
from picoparse import one_of
from picoparse import optional
from picoparse import remaining
from picoparse.text import whitespace
from picoparse.text import caseless_string

from ..models import Incoming
from ..parser import FormatError

class Echo(Incoming):
    @staticmethod
    def parse():
        one_of('+')
        caseless_string('echo')
        whitespace()

        return {
            'echo': "".join(remaining())
            }

    def handle(self, echo=None):
        self.reply(echo)

class Empty(Incoming):
    @staticmethod
    def parse():
        if optional(any_token, None):
            fail()

    def handle(self):
        self.reply(u"You sent a message with no text.")

class Error(Incoming):
    @staticmethod
    def parse():
        one_of('+')
        caseless_string('error')
        raise FormatError("error")

class Break(Incoming):
    @staticmethod
    def parse():
        one_of('+')
        caseless_string('break')

    def __init__(self, *args, **kwargs):
        raise RuntimeError("Broken")

class Improper(Incoming):
    @staticmethod
    def parse():
        one_of('+')
        caseless_string('improper')
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("".join(remaining()))

class Hello(Incoming):
    @staticmethod
    def parse():
        one_of('+')
        caseless_string('hello')

    def handle(self):
        pass
