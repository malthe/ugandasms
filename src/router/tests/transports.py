from router.transports import Transport

class Dummy(Transport):
    name = None

    def __init__(self, name, options):
        type(self).name = name
