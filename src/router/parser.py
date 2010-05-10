import re

from django.db.models import get_model

from .models import NotUnderstood
from .models import Broken

def require_model(name):
    spec = name.split('.')
    if len(spec) != 2:
        raise ValueError(
            "Model spec must be on the form '<app_label>.<model_name>` (got: '%s')" % name)
    model = get_model(*spec)
    if model is None:
        raise ValueError(
            "Model not found: %s." % name)
    return model

class Parser(object):
    """Parse text into message object."""

    def __init__(self, patterns):
        self.patterns = [
            (re.compile(pattern, re.IGNORECASE | re.UNICODE).match, require_model(name))
            for (pattern, name) in patterns]

    def __call__(self, text):
        text = text.strip()
        text = unicode(text)

        for matcher, factory in self.patterns:
            m = matcher(text)
            if m is not None:
                try:
                    return factory(text=text, **m.groupdict())
                except Exception, exc:
                    return Broken(text=unicode(exc), factory=factory.__name__)

        return NotUnderstood(text=text)
