import re
import webob

from .orm import Session

def camelcase_to_underscore(str):
    return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', str).lower().strip('_')

class Handler(object):
    def __init__(self, queue):
        self.queue = queue

    def __call__(self, message):
        kind = camelcase_to_underscore(message.__class__.__name__)

        # record message
        session = Session()
        session.add(message)

        try:
            method = getattr(self, 'handle_%s' % kind)
        except AttributeError:
            response = webob.Response(
                "No handler available for message kind ``%s``." % kind, status=200)
        else:
            response = method(message)

        try:
            session.commit()
        except:
            session.rollback()
            raise

        message.reply = response.body
        return response

    def enqueue(self, recipient, text):
        self.queue.put((recipient, text))

