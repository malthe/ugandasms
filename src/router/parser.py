import re

from .models import Message
from .exc import InvalidMessage

class NotUnderstood(Message):
    """Any message which was not understood."""

class Invalid(Message):
    """An invalid message."""

class Parser(object):
    """Parse text into message object."""

    def __init__(self, patterns):
        self.patterns = [
            (re.compile(pattern, re.IGNORECASE).match, factory)
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
                    return Invalid(str(exc))

        return NotUnderstood(text)
