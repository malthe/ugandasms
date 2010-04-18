import re

from .models import Incoming
from .exc import InvalidMessage

class NotUnderstood(Incoming):
    """Any message which was not understood."""

class Invalid(Incoming):
    """An invalid message."""

class Parser(object):
    """Parse text into message object."""

    def __init__(self, patterns):
        self.patterns = [
            (re.compile(pattern, re.IGNORECASE | re.UNICODE).match, factory)
            for (pattern, factory) in patterns]

    def __call__(self, text):
        text = text.strip()
        text = unicode(text)

        for matcher, factory in self.patterns:
            m = matcher(text)
            if m is not None:
                try:
                    return factory(text, **m.groupdict())
                except InvalidMessage, exc:
                    return Invalid(unicode(exc))

        return NotUnderstood(text)
