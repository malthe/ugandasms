import string

from picoparse import commit
from picoparse import many1
from picoparse import one_of
from picoparse import partial
from picoparse import remaining
from picoparse.text import whitespace

from router import pico
from router.models import Form
from router.router import FormatError

class NotUnderstood(Form):
    @pico.wrap
    def parse(cls):
        one_of('+')
        commit()
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
