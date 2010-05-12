from django.db import models
from polymorphic import PolymorphicModel as Model

from picoparse import any_token
from picoparse import many
from picoparse import one_of
from picoparse.text import whitespace1
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

class Break(Echo):
    class Meta:
        proxy = True

    @staticmethod
    def parse():
        one_of('+')
        caseless_string('break')
        string = "".join(many(any_token))
        return {
            'bad_argument': string,
            }

