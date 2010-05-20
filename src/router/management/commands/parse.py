from django.core.management.base import BaseCommand
from router.transports import Transport
from router.parser import ParseError
from pprint import pformat

class Command(BaseCommand):
    args = 'text'
    help = 'Parses the provided text message'

    def handle(self, text, **options):
        transport = Transport("script")
        messages = []
        while text:
            try:
                model, data, text = transport.parse(text)
            except ParseError, error:
                print error
                break
            else:
                messages.append((model, data))

        justification = max([len(model.__name__) for (model, data) in messages])
        for model, data in messages:
                print "%s: %s" % (model.__name__.ljust(justification), pformat(data))
