from django.dispatch import Signal
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from django.db.models import get_model
from django.db.models import get_models
from django.utils.functional import memoize

pre_handle = Signal(providing_args=["error", "result"])
post_handle = Signal(providing_args=["error"])

class FormatError(Exception):
    """Raised inside a parser to indicate a formatting error. The
    provided ``text`` will be used as the message reply.
    """

    def __init__(self, text):
        self.text = text

class Sequential(object):
    """Parse messages in sequence and handles first match.

    The router goes through the list of form models defined in the
    ``FORMS`` setting in Django's settings module, attempting to parse
    each on in sequence.

    Each item in the setting should be a string on the format::

      [<app_label>.]<model_name>

    The application label may be omitted if there's no ambiguity.

    When using the sequential router, forms are required to provide a
    parse method:

    .. classmethod:: parse(cls, text)

       Return a non-trivial result if ``text`` parses and a string
       containing any remaining text, or raise :class:`FormatError` to
       indicate a formatting error.

    See :func:`router.pico.wrap` for a convenient decorator for
    parsing with the :mod:`picoparse` library.

    If there's remaining text to parse, the operation is repeated.
    """

    _cache = {}

    @property
    def forms(self):
        try:
            paths = getattr(settings, "FORMS")
        except AttributeError: # pragma: NOCOVER
            raise ImproperlyConfigured(
                "Missing setting ``FORMS``.")

        return self._get_forms(paths)

    def _get_forms(paths):
        forms = []
        models = get_models()
        for path in paths:
            if path.count('.') == 0:
                for model in models:
                    if model.__name__ == path:
                        break
                else: # pragma: NOCOVER
                    raise ImproperlyConfigured("Model not found: %s." % path)
            elif path.count('.') == 1: # pragma: NOCOVER
                model = get_model(*path.split('.'))
            else: # pragma: NOCOVER
                raise ImproperlyConfigured(
                    "Specify messages as [<app_label>.]<model_name>.")
            if model is None: # pragma: NOCOVER
                raise ImproperlyConfigured("Can't find model: %s." % path)

            forms.append(model)
        return forms

    _get_forms = staticmethod(memoize(_get_forms, _cache, 1))

    def parse(self, text):
        """Parse the text provided in ``text``."""

        remaining = text

        while True:
            text = remaining.strip()
            error = None
            result = None
            remaining = ""

            for cls in self.forms:
                try:
                    result, remaining = cls.parse(text)
                    if result is None:
                        continue
                except FormatError, error:
                    pass

                yield cls, result, text[:-len(remaining) or None], error
                break

            # stop when there's no more text to parse
            if not remaining:
                break

    def route(self, message):
        """Route the message provided."""

        for cls, result, text, error in self.parse(message.text):
            erroneous = bool(error)
            form = cls(text=text, message=message, erroneous=erroneous)
            form.save()

            if result is not None:
                pre_handle.send(sender=form, result=result, error=error)
                error = None
                try:
                    form.handle(**result)
                except Exception, error:
                    raise
                finally:
                    post_handle.send(sender=form, error=error)
            elif error is not None:
                form.reply(error.text)
