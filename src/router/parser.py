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

from .models import NotUnderstood

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
    as the reply string."""

    def __init__(self, text):
        NoMatch.__init__(self, text)

class Parser(object):
    """Returns ``(model, data)`` for a message body.

    The ``model`` is a database message model that inherits from
    ``Incoming`` and ``data`` contain keyword arguments for the
    message handler.

    >>> parser = Parser(models)
    >>> model, data = parser(text)
    >>> message = model(text=text)
    >>> message.handle(**data)

    Participating models must provide a static method ``parse`` which
    should be a ``picoparse`` parse function. The result of this
    function is used as the ``data`` dictionary (although if the
    function returns ``None``, an empty dictionary is used).

    If no parser matched the input text, a ``NotUnderstood`` object is
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
            except ParseError:
                raise
            except NoMatch:
                continue

            if remaining:
                raise ParseError(remaining)

            return model, kwargs or {}

        return NotUnderstood, {}
