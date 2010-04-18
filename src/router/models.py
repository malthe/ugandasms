from sqlalchemy import Column
from sqlalchemy import types
from sqlalchemy.orm import relation
from sqlalchemy.orm import backref
from sqlalchemy.schema import ForeignKey

from .orm import Base

class Message(Base):
    """SMS message.

    The ``text`` attribute contains the original text.
    """

    id = Column(types.Integer, primary_key=True)
    sender = Column(types.String(12))
    receiver = Column(types.String(12))
    text = Column(types.Unicode(160))
    time = Column(types.DateTime, nullable=True)
    kind = Column(types.String(25))

    __tablename__ = "messages"
    __mapper_args__ = {
        'polymorphic_on': kind,
        'polymorphic_identity': None,
        'with_polymorphic': '*',
        }

    def __init__(self, text, **kwargs):
        self.text = text
        self.kind = self.__mapper_args__.get('polymorphic_identity')
        self.__dict__.update(kwargs)
        super(Message, self).__init__()

    @property
    def title(self):
        return self.text

class Delivery(Base):
    """Message delivery confirmation (DLR)."""

    __tablename__ = "deliveries"

    id = Column(types.Integer, primary_key=True)
    time = Column(types.DateTime)
    message_id = Column(types.Integer, ForeignKey(Message.id), unique=True)
    message = relation(
        Message, primaryjoin=(message_id==Message.id),
        uselist=False, backref=backref(
            'delivery', uselist=False))
    status = Column(types.Integer)

    @property
    def success(self):
        return self.status == 1

class Incoming(Message):
    """An incoming message."""

    __tablename__ = "incoming"

    id = Column(types.Integer, ForeignKey(Message.id), primary_key=True)
    reply = Column(types.Unicode(160))

class Outgoing(Message):
    """An outgoing message."""
