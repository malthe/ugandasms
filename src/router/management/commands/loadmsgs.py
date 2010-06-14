import yaml
import iso8601

from django.core.management.base import BaseCommand

from .handle import handle

class Command(BaseCommand):
    help = 'Load messages from yaml format'

    def handle(self, path, **options):
        body = open(path).read()
        for index, entry in enumerate(yaml.load(body)):
            time = iso8601.parse_date(entry['time'])
            name, ident = entry['uri'].split('://')
            handle(ident, entry['text'], time=time, name=name)
