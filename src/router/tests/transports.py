from router.transports import Message

class Dummy(Message):
    name = None

    def __init__(self, name="dummy"):
        type(self).name = name
        Message.__init__(self, name)
