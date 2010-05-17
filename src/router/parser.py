from picoparse import choice
from picoparse import commit
from picoparse import many
from picoparse import many1
from picoparse import one_of
from picoparse import not_one_of
from picoparse import optional
from picoparse import partial
from picoparse import run_parser
from picoparse import tri
from picoparse import NoMatch
from picoparse.text import caseless_string
from picoparse.text import whitespace
from string import digits as digit_chars

comma = partial(one_of, ',')
dot = partial(one_of, '.')
not_comma = partial(not_one_of, ',')
digits = partial(many1, partial(one_of, digit_chars))

def float_digits():
    """Parses a floating point number.

    >>> "".join(run_parser(float_digits, '123')[0])
    '123'

    >>> "".join(run_parser(float_digits, '123.0')[0])
    '123.0'

    >>> "".join(run_parser(float_digits, '123,0')[0])
    '123.0'

    >>> "".join(run_parser(float_digits, '.123')[0])
    '.123'
    """

    number = optional(digits, [])

    @tri
    def decimals():
        sep = choice(comma, dot)
        commit()
        try:
            return ["."] + digits()
        except:
            raise ParseError("Expected decimals after '%s'." % sep)

    if not number:
        number = decimals()
    else:
        number += optional(decimals, [])

    return number

def one_of_strings(*strings):
    """Parses one of the strings provided, caseless.

    >>> "".join(run_parser(
    ...     partial(one_of_strings, 'abc', 'def'), 'abc')[0])
    'abc'

    >>> "".join(run_parser(
    ...     partial(one_of_strings, 'abc', 'def'), 'def')[0])
    'def'
    """

    return choice(*map(tri, map(partial(partial, caseless_string), strings)))

def next_parameter(parser=partial(many, not_comma)):
    """Read the next parameter on a comma-separated input.

    >>> "".join(run_parser(next_parameter, ', abc')[0])
    'abc'

    >>> "".join(run_parser(next_parameter, 'abc')[0])
    'abc'

    >>> "".join(run_parser(partial(next_parameter, digits), ', 123')[0])
    '123'
    """

    optional(comma, None)
    whitespace()
    return "".join(parser())

class ParseError(NoMatch):
    """Should be raised inside a parser function to return a reply
    that the message was not understood. The provided argument is used
    as the reply string."""

    def __init__(self, text):
        NoMatch.__init__(self, text)

class Parser(object):
    """Returns ``(model, data)`` for a message body.

    The ``model`` is a message model that inherits from ``Incoming``
    and ``data`` contain keyword arguments for the message handler.

    Models are required to implement parser functions from the
    :mod:`picoparse` library.

    >>> import picoparse
    >>> import picoparse.text

    Here's an example of a greeting model:

    >>> class Greeting(object):
    ...     @staticmethod
    ...     def parse():
    ...         one_of('+')
    ...         picoparse.text.caseless_string('hello')
    ...         picoparse.text.whitespace1()
    ...         remaining = picoparse.remaining()
    ...         return {
    ...             'name': ''.join(remaining)
    ...         }
    ...
    ...     def handle(self, name=None):
    ...         return u'Hello, %s!' % name

    You won't usually need to use the ``Parser`` class manually; the
    *transport* abstraction exposes this component on a higher
    level. However, the following snippet outlines its operation:

    >>> parser = Parser((Greeting,))          # set up parser
    >>> model, data = parser('+hello world')  # parse text
    >>> message = model()                     # create message
    >>> message.handle(**data)                # handle message
    u'Hello, world!'

    Participating models must provide a static method ``parse`` which
    should be a ``picoparse`` parse function. The result of this
    function is used as the ``data`` dictionary (although if the
    function returns ``None``, an empty dictionary is used).

    Raises ``ParseError`` if no parser matched the input text.
    """

    def __init__(self, models):
        self.models = filter(lambda m: hasattr(m, 'parse'), models)

    def __call__(self, text):
        text = text.strip()
        text = unicode(text)
        source = tuple(text) or ("", )

        for model in self.models:
            parser = model.parse

            try:
                kwargs, remaining = run_parser(parser, source)
            except ParseError:
                raise
            except NoMatch:
                continue
            except Exception, exc: # pragma: NOCOVER
                # backwards compatible with older version of picoparse
                if 'Commit / cut called' in str(exc):
                    raise ParseError(text)
                raise

            if remaining:
                msg = "".join(remaining)
                raise ParseError(msg)

            return model, kwargs or {}

        raise ParseError(text)
