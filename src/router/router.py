from django.dispatch import Signal
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from django.db.models import get_model
from django.db.models import get_models
from django.utils.functional import memoize

from .models import Form

pre_parse = Signal()
post_parse = Signal(providing_args=["error"])
pre_handle = Signal(providing_args=["result"])
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

    def route(self, message):
        pre_parse.send(sender=message)
        remaining = unicode(message.text)

        while True:
            text = remaining.strip()
            error = None
            result = None
            remaining = ""

            form = Form(text=text, message=message)
            for cls in self.forms:
                try:
                    result, remaining = cls.parse(form.text)
                    if result is None:
                        continue
                except FormatError, error:
                    pass

                erroneous = bool(error)
                form.__class__ = cls
                form.__init__(text=text, message=message, erroneous=erroneous)
                post_parse.send(sender=form, error=error)
                form.save()

                if result is not None:
                    pre_handle.send(sender=form, result=result)
                    error = None
                    try:
                        form.handle(**result)
                    except Exception, error:
                        pass
                    finally:
                        post_handle.send(sender=form, error=error)
                elif error is not None:
                    form.reply(error.text)

            # stop when there's no more text to parse
            if not remaining:
                break
