import collections

from sqlalchemy import Column
from sqlalchemy import types

from router.orm import Base

Group = collections.namedtuple("Group", "name, mask")

GROUPS = {
    'VHT': Group("Village Health Team", 0b00000001),
    'HCW': Group("Health Center Worker", 0b00000011),
    'ADM': Group("Administrator", 0b11111111),
    }

class User(Base):
    __tablename__ = 'users'

    id = Column(types.Integer, primary_key=True)
    number = Column(types.String(12), unique=True)
    name = Column(types.Unicode(50), nullable=True)
    location = Column(types.Unicode(50), nullable=True)
    mask = Column(types.Integer, default=0)

    def __unicode__(self):
        return self.name
