import re

from sqlalchemy import Column
from sqlalchemy import types

from .orm import Base

NETWORKS = tuple((name, re.compile(pattern)) for (name, pattern) in 
                 (('MTN', '^(\+?256|0)(78|77|39)$'),
                  ('UTL', '^(\+?256|0)(71)$'),
                  ('Orange', '^(\+?256|0)(79)$'),
                  ('Orange', '^(\+?256|0)(75)$'),
                  ('Warid', '^(\+?256|0)(70)$'),))

class Message(Base):
    """Represents an SMS message.

    The ``text`` attribute contains the original text.
    """

    __tablename__ = "messages"

    id = Column(types.Integer, primary_key=True)
    sender = Column(types.String(12))
    receiver = Column(types.String(12))
    text = Column(types.String(160))
    reply = Column(types.String(160), nullable=True)
    state = Column(types.Integer, default=0)
    time = Column(types.DateTime)
    kind = Column(types.String(20))

    def __init__(self, text, sender=None, reply=None, kind=None, **kwargs):
        self.__dict__.update(kwargs)
        super(Message, self).__init__(
            text=text, sender=sender, reply=reply, kind=kind)

    def get_summary(self):
        for network, pattern in NETWORKS:
            if pattern.match(self.sender):
                break
        else:
            network = None

        return {
            'text': self.text,
            'sender': self.sender,
            'network': network,
            'time': self.time.strftime("%A, %d. %B %Y %I:%M %p"),
            }
