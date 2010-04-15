from webob.dec import wsgify
from webob import Response
from datetime import datetime

STATUS_DENIED = -2
STATUS_UNKNOWN = -1
STATUS_ACCEPTED = 0
STATUS_QUEUED = 3

class WSGIApp(object):
    """Kannel HTTP service.

    This object implements the WSGI application interface.
    """

    def __init__(self, parser, handler):
        self.parser = parser
        self.handler = handler

    @wsgify
    def __call__(self, request):
        try:
            sender = request.params['sender']
            receiver = request.params['receiver']
            delivery = int(request.params.get('delivery', -1))
            text = request.params['text']
            time = datetime.utcfromtimestamp(
                float(request.params['timestamp']))
        except Exception, e:
            return Response(
                "There was an error (``%s``) processing the request: %s." % (
                    type(e).__name__, str(e)), content_type="text/plain")

        if delivery != -1:
            # todo: delivery report
            return Response("")

        message = self.parser(text)
        message.sender = sender
        message.receiver = receiver
        message.time = time

        return self.handler(message)
