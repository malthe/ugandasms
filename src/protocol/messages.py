from sqlalchemy.orm import relation
from sqlalchemy.orm import backref

from router.models import Message

from .models import User

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
