import re

from sqlalchemy.orm import relation
from sqlalchemy.orm import backref
from sqlalchemy import Column
from sqlalchemy import types

from router.models import Message

from .models import User
from .models import GROUPS

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

class Registration(UserMessage):
    """Register with the system."""

    title = u"Registration"

class HealthWorkerSignup(UserMessage):
    """Register as health worker."""

    mask = User.mask
    facility = Column(types.Integer())

    def __init__(self, text, role=None, facility=None):
        group = GROUPS.get(role.upper(), None)
        if group is None:
            raise ValueError("Role unknown: %s." % role)

        self.text = text
        self.mask = group.mask
        self.facility = facility

    @property
    def group(self):
        for group in GROUPS.values():
            if group.mask == self.mask:
                return group

    @property
    def title(self):
        return "VHT: %d" % self.facility

for cls in locals().values():
    if isinstance(cls, type) and issubclass(cls, Message):
        args = cls.__mapper_args__ = cls.__mapper_args__.copy()
        kind = cls.kind = camelcase_to_underscore(cls.__name__)
        args['polymorphic_identity'] = kind
