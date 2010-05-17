from django.http import HttpResponse as Response
from .transports import get_transport

def kannel(request, name='kannel'):
    """Kannel incoming view.

    The default transport name is "kannel"; to use this view with a
    different transport name, simply define a wrapper view function that
    calls this function with the right ``name`` argument.

    Example:

      >>> from functools import partial
      >>> custom_kannel = partial(kannel, name='custom')

    Note that this view is just a paper-thin wrapper around the
    ``Kannel`` transport.
    """

    transport = get_transport('kannel')

    try:
        transport.handle(request)
    except Exception, e:
        return Response(
            "There was an error (``%s``) processing the request: %s." % (
                type(e).__name__, str(e)), content_type="text/plain",
            status="406 Not Acceptable")

    return Response(u"")
