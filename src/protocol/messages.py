import re

from sqlalchemy.orm import relation
from sqlalchemy.orm import backref

from router.models import Message

from .models import User

def camelcase_to_underscore(str):
    return re.sub(
        '(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1',
        str).lower().strip('_')

class UserMessage(Message):
    user = relation(
        User, primaryjoin=(Message.sender==User.number),
        foreign_keys=[User.number],
        uselist=False, backref=backref(
            'messages', uselist=True, order_by=Message.time),
        )

class Empty(UserMessage):
    """The empty message."""

class Register(UserMessage):
    """Register with the system."""

    title = u"Registration"

class Approve(UserMessage):
    """Approve user to join group."""

for cls in locals().values():
    if isinstance(cls, type) and issubclass(cls, Message):
        args = cls.__mapper_args__ = cls.__mapper_args__.copy()
        kind = cls.kind = camelcase_to_underscore(cls.__name__)
        args['polymorphic_identity'] = kind
