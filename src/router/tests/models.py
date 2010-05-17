from picoparse import one_of
from picoparse.text import caseless_string

from ..models import Echo
from ..parser import ParseError

class Error(Echo):
    class Meta:
        proxy = True

    @staticmethod
    def parse():
        one_of('+')
        caseless_string('error')
        raise ParseError("error")
