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
    return transport.handle(request)
