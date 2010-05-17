from picoparse import one_of
from picoparse.text import caseless_string

from ..models import Incoming
from ..parser import ParseError

class Error(Incoming):
    @staticmethod
    def parse():
        one_of('+')
        caseless_string('error')
        raise ParseError("error")

class Break(Incoming):
    @staticmethod
    def parse():
        one_of('+')
        caseless_string('break')

    def __init__(self, *args, **kwargs):
        raise RuntimeError("Broken")
