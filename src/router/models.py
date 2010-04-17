from sqlalchemy import Column
from sqlalchemy import types

from .orm import Base

class Message(Base):
    """Represents an SMS message.

    The ``text`` attribute contains the original text.
    """

    id = Column(types.Integer, primary_key=True)
    sender = Column(types.String(12))
    receiver = Column(types.String(12))
    text = Column(types.Unicode(160))
    reply = Column(types.Unicode(160), nullable=True)
    state = Column(types.Integer, default=0)
    time = Column(types.DateTime)
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
