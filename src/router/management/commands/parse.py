from django.core.management.base import BaseCommand
from router.transports import Message
from pprint import pformat

class Command(BaseCommand):
    args = 'text'
    help = 'Parses the provided text message'

    def handle(self, text, **options):
        transport = Message("script")
        forms = []

        for cls, result, text, error in transport.router.parse(text):
            if error is not None:
                print error.text
                return

            forms.append((cls, result))

        if forms:
            justification = max(
                [len(model.__name__) for (model, data) in forms])

            for model, data in forms:
                print "%s: %s" % (
                   model.__name__.ljust(justification), pformat(data))
        else:
            print "No forms matched."
