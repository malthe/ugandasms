import os
import pwd

from django.core.management.base import BaseCommand
from router.transports import Message

def handle(ident, text, time=None, name="script"):
    transport = Message(name)
    message = transport.incoming(ident, text, time)
    forms = message.forms.all()
    for i, form in enumerate(forms):
        print "%d/%d %s" % (i+1, len(forms), message.time.isoformat())
        print "--> %s" % form.text
        print "----" + "-"*len(form.text)

        replies = form.replies.all()
        for j, reply in enumerate(replies):
            print "    %d/%d %s" % (j+1, len(replies), reply.uri)
            print "    <-- %s" % reply.text

class Command(BaseCommand):
    args = 'text'
    help = 'Parses the provided text message and handles it'

    def handle(self, text, **options):
        try:
            user = os.getlogin()
        except OSError:
            user = pwd.getpwuid(os.geteuid())[0]

        handle(user, text)

