import os
import csv
import imp
import sys
import iso8601

from django import conf

def install_demo():
    try:
        settings = sys.argv[1]
    except IndexError:
        print "Error: Must provide path to settings module (e.g. ``settings.py``)"
        sys.exit(1)

    imp.load_source("settings", settings)
    settings = conf.Settings("settings")
    conf.settings.configure(settings)

    from router.models import camelcase_to_dash
    from router.models import Incoming
    from router.transports import Transport

    transport = Transport("fixture", {})

    settings.TRANSPORTS["fixture"] = {
        'TRANSPORT': transport,
        }

    path = os.path.join(os.path.dirname(__file__), "demo.csv")
    reader = csv.reader(open(path), delimiter='\t')
    for line in reader:
        line = filter(None, line)
        line = map(unicode, line)
        if not line:
            continue
        if line[0].strip().startswith('#'):
            continue
        try:
            sender, receiver, text, date = line
        except ValueError, e:
            print "- Skipping %s (%s)." % (repr(line), str(e))
            continue
        time = iso8601.parse_date(date)

        transport.incoming(sender, text, time)
        message = Incoming.objects.order_by('pk')[0]

        print "%s >>> %s [%s]" % (
            sender, text, camelcase_to_dash(message.__class__.__name__))
        for reply in message.replies.all():
            print "%s <<< %s" % (sender, reply.text)

    from router.models import Message
    print "%d messages recorded." % Message.objects.count()
