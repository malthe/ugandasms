from django.core.management.base import BaseCommand
from router.transports import Message
from pprint import pformat

class Command(BaseCommand):
    args = 'text'
    help = 'Parses the provided text message'

    def handle(self, text, **options):
        transport = Message("script")
        messages = []

        for cls, result, text, error in transport.router.parse(text):
            if error is not None:
                print error.text
                break
            messages.append((cls, result))

        justification = max([len(model.__name__) for (model, data) in messages])
        for model, data in messages:
                print "%s: %s" % (
                    model.__name__.ljust(justification), pformat(data))
