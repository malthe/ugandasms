import datetime
import itertools

from string import digits as digit_chars
from string import ascii_letters

from picoparse import choice
from picoparse import fail
from picoparse import many1
from picoparse import n_of
from picoparse import one_of
from picoparse import not_one_of
from picoparse import optional
from picoparse import partial
from picoparse import run_parser
from picoparse import sep
from picoparse import tri
from picoparse import NoMatch
from picoparse.text import caseless_string
from picoparse.text import lexeme
from picoparse.text import whitespace

comma = partial(one_of, ',')
dot = partial(one_of, '.')
hash = partial(one_of, '#')
not_comma = partial(not_one_of, ',')
digit = partial(one_of, digit_chars)
digits = partial(many1, digit)

_unit_days_multiplier = {
    'd': 1,
    'w': 7,
    'm': 30,
    'y': 365,
    }

_short_months = [datetime.date(1900, i, 1).strftime('%b') for i in range(1, 13)]
_long_months = [datetime.date(1900, i, 1).strftime('%B') for i in range(1, 13)]

_date_format_mapping = {
    '-': partial(one_of, '-'),
    ',': partial(one_of, ','),
    '.': partial(one_of, '.'),
    ' ': partial(one_of, ' '),
    '/': partial(one_of, '/'),
    'Y': partial(n_of, digit, 4),
    'y': partial(n_of, digit, 2),
    'm': digits,
    'd': digits,
    'b': partial(choice, *map(tri, map(partial(partial, caseless_string), _short_months))),
    'B': partial(choice, *map(tri, map(partial(partial, caseless_string), _long_months))),
    }

def _parse_date_format(date_format):
    tokens = tuple(date_format.replace('%', ''))
    parsers = map(tri, map(_date_format_mapping.get, tokens))
    date_string = "".join(itertools.chain(*[parser() for parser in parsers]))
    try:
        return datetime.datetime.strptime(date_string, date_format)
    except:
        fail()

def separator(parser=comma):
    """Expects a comma separation.

    >>> "".join(run_parser(separator, ', ')[0])
    ','
    >>> "".join(run_parser(separator, ' ,')[0])
    ','
    """

    return lexeme(parser)

def date(formats=("%m/%d/%Y",)):
    """Parses a date using one of the supplied formats.

    To integrate with Django's date format settings, pass in the
    ``DATE_INPUT_FORMATS`` setting:

    >>> from django.conf import settings
    >>> django_date_parser = partial(date, formats=settings.DATE_INPUT_FORMATS)

    The standard settings enables a wide set of input formats; we
    demonstrate some of them here:

    >>> run_parser(django_date_parser, '12/31/1999')[0].isoformat()
    '1999-12-31T00:00:00'
    >>> run_parser(django_date_parser, 'December 31, 1999')[0].isoformat()
    '1999-12-31T00:00:00'
    >>> run_parser(django_date_parser, '12/31/99')[0].isoformat()
    '1999-12-31T00:00:00'
    """

    parsers = [partial(_parse_date_format, f) for f in formats]
    return choice(*map(tri, parsers))

def timedelta():
    """Parses a time quantity into a :mod:`datetime.timedelta` instance.

    >>> run_parser(timedelta, '7 days')[0].days
    7
    >>> run_parser(timedelta, '7d')[0].days
    7
    >>> run_parser(timedelta, '1w')[0].days
    7
    >>> run_parser(timedelta, '6 months')[0].days
    180
    >>> run_parser(timedelta, '1 year')[0].days
    365
    """

    number = int("".join(digits()))

    def unit():
        whitespace()
        unit = one_of_strings('day', 'week', 'month', 'year', 'd', 'w', 'm', 'y', )[0]
        optional(partial(one_of, 's'), None)
        return unit

    multiplier = _unit_days_multiplier[unit()]
    return datetime.timedelta(days=multiplier*number)

def floating():
    """Parses a floating point number.

    >>> "".join(run_parser(floating, '123')[0])
    '123'
    >>> "".join(run_parser(floating, '123.0')[0])
    '123.0'
    >>> "".join(run_parser(floating, '123,0')[0])
    '123.0'
    >>> "".join(run_parser(floating, '.123')[0])
    '.123'
    >>> "".join(run_parser(floating, '123.')[0])
    '123.'

    """

    number = optional(digits, [])
    if optional(partial(choice, comma, dot), None):
        number += "."
    number += optional(digits, [])
    return number

def next_parameter(parser=partial(many1, not_comma)):
    """Read the next parameter on a comma-separated input.

    >>> "".join(run_parser(next_parameter, ', abc')[0])
    'abc'
    >>> "".join(run_parser(next_parameter, ' , abc')[0])
    'abc'
    >>> "".join(run_parser(partial(next_parameter, digits), ', 123')[0])
    '123'
    """

    whitespace()
    comma()
    whitespace()
    return parser()

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

def tag():
    """Parse a single tag, optionally prefixed by a hash mark
    (``'#'``).
    """

    optional(hash, None)
    return many1(partial(one_of, ascii_letters))

def tags():
    """Parse one or more tags, each separated by whitespace and/or a
    comma.

    >>> run_parser(tags, 'abc, def')[0]
    ['abc', 'def']
    >>> run_parser(tags, '#abc #def')[0]
    ['abc', 'def']
    """

    return map(partial("".join), sep(tag, partial(many1, partial(one_of, ' ,'))))

class ParseError(NoMatch):
    """Shoud be used inside parser functions to handle (human) errors
    gracefully; the provided ``text`` argument is used as the reply
    string.

    >>> error = ParseError('An error occurred.')
    >>> print error.text
    An error occurred.
    """

    def __init__(self, text):
        NoMatch.__init__(self, text)
        self.text = text

class Parser(object):
    """Returns ``(model, data, remaining)`` for a message body.

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

    >>> parser = Parser((Greeting,))                    # set up parser
    >>> model, data, remaining = parser('+hello world') # parse text
    >>> message = model()                               # create message
    >>> message.handle(**data)                          # handle message
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

            return model, kwargs or {}, "".join(remaining)

        raise ParseError(text)
