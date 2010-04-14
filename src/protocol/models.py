import collections

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy import types

from router.orm import Base

Group = collections.namedtuple("Group", "name, mask")

GROUPS = {
    'VHT': Group("Village Health Team", 0b00000001),
    'HC2': Group("Health Center II group", 0b00000011),
    'HC3': Group("Health Center III group", 0b00000101),
    'HC4': Group("Health Center IV group", 0b00001001),
    'ADM': Group("administrators' group", 0b10001111),
    }

class User(Base):
    __tablename__ = 'users'

    id = Column(types.Integer, primary_key=True)
    name = Column(types.Unicode(50))
    location = Column(types.Unicode(50), nullable=True)
    number = Column(types.String(12))
    mask = Column(types.Integer, default=0)

