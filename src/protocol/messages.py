from sqlalchemy.orm import relation
from sqlalchemy.orm import backref
from sqlalchemy import Column
from sqlalchemy import types

from router.models import Message

from .models import User
from .models import GROUPS

class UserMessage(Message):
    user = relation(
        User, primaryjoin=(Message.sender==User.number),
        foreign_keys=[User.number],
        uselist=False, backref=backref(
            'messages', uselist=True, order_by=Message.time),
        )

class Empty(UserMessage):
    """The empty message."""

class Registration(UserMessage):
    """Register with the system."""

    title = u"Registration"
    location = Column(types.Unicode(25), nullable=True)

class HealthWorkerSignup(UserMessage):
    """Register as health worker."""

    mask = Column(types.Integer)
    facility = Column(types.Integer())

    def __init__(self, text, role=None, facility=None):
        group = GROUPS.get(role.upper(), None)
        if group is None:
            raise ValueError("Role unknown: %s." % role)

        super(HealthWorkerSignup, self).__init__(
            text, mask=group.mask, facility=facility)

    @property
    def group(self):
        for group in GROUPS.values():
            if group.mask == self.mask:
                return group

    @property
    def title(self):
        return u"Signup as %s" % self.group.name
