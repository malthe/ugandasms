from django.db import models
from polymorphic import PolymorphicModel as Model

from picoparse import any_token
from picoparse import many
from picoparse import one_of
from picoparse.text import whitespace
from picoparse.text import whitespace1
from picoparse.text import caseless_string

from ..models import Incoming
from ..parser import ParseError

class User(Model):
    number = models.CharField(max_length=12, unique=True)

    class Meta:
        app_label = 'router'

class Echo(Incoming):
    @staticmethod
    def parse():
        one_of('+')
        caseless_string('echo')
        whitespace1()
        return {
            'text': "".join(many(any_token))
            }

    def handle(self):
        return self.text

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

