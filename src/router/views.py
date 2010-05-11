from datetime import datetime
from django.http import HttpResponse as Response
from django.conf import settings
from django.db.models import get_models
from django.core.exceptions import ObjectDoesNotExist
from .parser import Parser
from .models import Delivery
from .models import Peer

def kannel(request):
    try:
        delivery = int(request.GET.get('delivery', 0))
        time = datetime.fromtimestamp(
            float(request.GET['timestamp']))

        if delivery:
            message_id = int(request.GET['id'])
        else:
            sender = request.GET['sender']
            text = request.GET['text']
    except Exception, e:
        return Response(
            "There was an error (``%s``) processing the request: %s." % (
                type(e).__name__, str(e)), content_type="text/plain",
            status="406 Not Acceptable")

    # handle delivery reports
    if delivery:
        report = Delivery(
            time=time, message_id=message_id, status=delivery)
        report.save()
        response = Response("")
    else:
        # to-do: cache this
        parser = Parser(get_models())

        # parse message
        message = parser(text)
        message.uri = "kannel://%s" % sender
        message.time = time

        try:
            peer = message.peer
        except ObjectDoesNotExist:
            peer = None

        if peer is None:
            Peer(uri=message.uri).save()

        # process and record reply
        reply = message.handle()
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
