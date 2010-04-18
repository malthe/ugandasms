import webob

class Handler(object):
    def __init__(self, queue):
        self.queue = queue

    def __call__(self, message):
        try:
            assert message.kind is not None
            name = message.kind.replace('-', '_')
            method = getattr(self, 'handle_%s' % name)
        except AttributeError:
            return webob.Response(
                "No handler available for message kind ``%s``." % message.kind)

        return method(message)

    def enqueue(self, recipient, text):
        self.queue.put((recipient, text))

