from datetime import datetime
from django.http import HttpResponse as Response
from django.conf import settings

from .parser import Parser
from .models import Delivery

def kannel(request):
    try:
        delivery = int(request.REQUEST.get('delivery', -1))
        time = datetime.fromtimestamp(
            float(request.REQUEST['timestamp']))

        # message send
        if request.method == 'POST':
            sender = request.POST['sender']
            receiver = request.POST['receiver']
            text = request.POST['text']

        # message delivery
        elif request.method == 'GET':
            message_id = int(request.GET['id'])
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
        # XXX: cache this
        parser = Parser(settings.PATTERNS)

        # parse message
        message = parser(text)
        message.sender = sender
        message.receiver = receiver
        message.time = time

        # process and record reply
        reply = message()
        message.reply = reply
        message.save()

        # prepare HTTP response
        response = Response(reply)

        # add delivery confirmation request
        response['X-Kannel-DLR-Url'] = (
            "%s?delivery=%%d&id=%d&timestamp=%%T" % (
                settings.DLR_URL, message.id))
        response['X-Kannel-DLR-Mask'] = "3"

    return response
