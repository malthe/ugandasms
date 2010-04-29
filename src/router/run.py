import os
import sys

from webob.dec import wsgify
from webob import Response
from datetime import datetime
from django.core.handlers.wsgi import WSGIHandler

from .models import Delivery

STATUS_DENIED = -2
STATUS_UNKNOWN = -1
STATUS_ACCEPTED = 0
STATUS_QUEUED = 3

# _application = django.core.handlers.wsgi.WSGIHandler()

# def application(environ, start_response):
#     environ['PATH_INFO'] = environ['SCRIPT_NAME'] + environ['PATH_INFO']
#     return _application(environ, start_response)

class WSGIApp(object):
    """Kannel HTTP service.

    POST requests

       These are messages that arrive from the SMS service.

    GET requests

       These are delivery confirmation requests.

    Note that this class implements the WSGI application interface.
    """

    def __init__(self, parser, handler, dlr_url=None):
        self.parser = parser
        self.handler = handler
        self.dlr_url = dlr_url

    @wsgify
    def __call__(self, request):
        try:
            delivery = int(request.params.get('delivery', -1))
            time = datetime.fromtimestamp(
                float(request.params['timestamp']))

            # message send
            if request.method == 'POST':
                sender = request.params['sender']
                receiver = request.params['receiver']
                text = request.params['text']
            # message delivery
            elif request.method == 'GET':
                message_id = int(request.params['id'])
        except Exception, e:
            return Response(
                "There was an error (``%s``) processing the request: %s." % (
                    type(e).__name__, str(e)), content_type="text/plain",
                status="406 Not Acceptable")

        # handle delivery reports
        if delivery != -1:
            report = Delivery(
                time=time, message_id=message_id, status=delivery)
            report.save()
            response = Response("")
        else:
            # parse message
            message = self.parser(text)
            message.sender = sender
            message.receiver = receiver
            message.time = time

            # record message and refresh
            # XXX session.flush()
            # XXX session.refresh(message)

            # add delivery confirmation request
            response = self.handler(message)
            response.headers['X-Kannel-DLR-Url'] = (
                "%s?delivery=%%d&id=%d&timestamp=%%T" % (
                    self.dlr_url, message.id))
            response.headers['X-Kannel-DLR-Mask'] = "3"

            # record reply
            message.reply = response.unicode_body
            message.save()

        # commit or rollback
        # try:
        #     session.commit()
        # except:
        #     session.rollback()
        #     raise

        return response
