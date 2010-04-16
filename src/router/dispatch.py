import re
import webob

from .orm import Session

class Handler(object):
    def __init__(self, queue):
        self.queue = queue

    def __call__(self, message):
        # record message
        session = Session()
        session.add(message)

        try:
            method = getattr(self, 'handle_%s' % message.kind)
        except AttributeError:
            response = webob.Response(
                "No handler available for message kind ``%s``." % message.kind)

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

