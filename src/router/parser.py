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
    """Returns ``(model, kwargs)`` for a message body.

    The ``model`` is a database message model that inherits from
    ``Incoming`` and ``kwargs`` are initialization arguments::

    >>> parser = Parser(models)
    >>> model, kwargs = parser(text)
    >>> message = model(**kwargs)

    Participating models must provide a static method ``parse`` which
    should be a ``picoparse`` parse function.

    The returned ``kwargs`` is either the return value of the parse
    function, or if it returns ``None``, a dictionary containing just
    an entry for ``'text'``. Note that ``kwargs`` will always return a
    value for ``'text'`` --- by default the message body.

    If a parser raises a ``ParseError`` exception, the first exception
    argument is used as the message text for a ``NotUnderstood``
    message. If the message was not parsed at all, a ``NotUnderstood``
    object is also returned.
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
                text = unicode(error.args[0])
                break
            except NoMatch:
                continue

            if remaining:
                text = u"".join(remaining)
            elif kwargs is None:
                kwargs = {'text': text}
            else:
                kwargs.setdefault("text", text)

            return model, kwargs

        return NotUnderstood, {'text': text}
