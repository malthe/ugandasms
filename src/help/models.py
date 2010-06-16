import string

from django.db import models

from picoparse import commit
from picoparse import fail
from picoparse import many1
from picoparse import one_of
from picoparse import partial
from picoparse import remaining
from picoparse.text import whitespace

from router import pico
from router.models import Form
from router.router import FormatError

class Input(models.Model):
    text = models.CharField(max_length=255)

class NotUnderstood(Form):
    @pico.wrap
    def parse(cls):
        if one_of('+'):
            commit()
        else:
            fail()
        whitespace()
        try:
            command = "".join(many1(partial(one_of, string.ascii_letters)))
        except:
            raise FormatError(
                "Expected command after \"+\" symbol (got: %s)." % \
                "".join(remaining()))

        whitespace()

        text = "".join(remaining()).strip()
        if text:
            text = " (additonal arguments: %s)." % text

        raise FormatError(
            "Unknown command: %s%s." % (command.upper(), text))

class FreeForm(Form):
    @pico.wrap
    def parse(cls):
        return {
            'text': "".join(remaining())
            }

    def handle(self, text=None):
        if not text.strip():
            self.reply(
                "We received an empty message. If this was a mistake, "
                "please try again.")
        else:
            Input(text=text).save()
            self.reply("We have received your input. Thank you.")
