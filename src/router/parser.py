from picoparse import choice
from picoparse import many
from picoparse import many1
from picoparse import one_of
from picoparse import not_one_of
from picoparse import partial
from picoparse import run_parser
from picoparse import tri
from picoparse import NoMatch
from picoparse.text import caseless_string
from picoparse.text import whitespace
from string import digits as digit_chars

from .models import Broken
from .models import NotUnderstood
from .models import camelcase_to_dash

comma = partial(one_of, ',')
not_comma = partial(not_one_of, ',')
digits = partial(many1, partial(one_of, digit_chars))

def one_of_strings(*strings):
    return choice(*map(tri, map(partial(partial, caseless_string), strings)))

def next_parameter(parser=not_comma):
    comma()
    whitespace()
    name = u"".join(many(parser))
    return name

class ParseError(NoMatch):
    """Should be raised inside a parser function to return a reply
    that the message was not understood. The provided argument is used
    as the reply string (as-is)."""

class Parser(object):
    """Parse text messages into message objects.

    The returned objects are Django database objects that can be
    stored using ``save()``.

    Participating models must provide a static method ``parse`` which
    should be a ``picoparse`` parse function.

    Its return value is passed as keyword arguments to the message
    constructor. The message text can be overrided by including a
    value for the 'text' key.

    If a parser raises a ``ParseError`` exception, the provided string
    is used as the text for a ``NotUnderstood`` message.

    If the message was not parsed at all, a ``NotUnderstood`` object
    is also returned. Meanwhile, if a message does parse but
    construction of the message fails, a ``Broken`` object is
    returned.
    """

    def __init__(self, models):
        self.models = filter(lambda m: hasattr(m, 'parse'), models)

    def __call__(self, text):
        text = text.strip()
        text = unicode(text)

        for model in self.models:
            parser = model.parse
            if parser is None:
                continue
            try:
                kwargs, remaining = run_parser(parser, text)
            except ParseError, error:
                msg, = error.args
                return NotUnderstood(text=unicode(msg))
            except NoMatch:
                continue

            if remaining:
                return NotUnderstood(text=u"".join(remaining))

            try:
                if kwargs is None:
                    return model(text=text)
                else:
                    kwargs.setdefault("text", text)
                    return model(**kwargs)
            except Exception, exc:
                return Broken(text=unicode(exc), kind=camelcase_to_dash(model.__name__))

        return NotUnderstood(text=text)
