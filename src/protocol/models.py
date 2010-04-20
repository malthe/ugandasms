import re
import collections

from sqlalchemy import Column
from sqlalchemy import types
from sqlalchemy.orm import relation
from sqlalchemy.orm import backref
from sqlalchemy.schema import ForeignKey

from router.orm import Base

Group = collections.namedtuple("Group", "name, mask")

GROUPS = {
    'VHT': Group("Village Health Team", 0b00000001),
    'HCW': Group("Health Center Worker", 0b00000011),
    'HCS': Group("Health Center Surveillance Officer", 0b00000111),
    'ADM': Group("Administrator", 0b11111111),
    }

NETWORKS = tuple((name, re.compile(pattern)) for (name, pattern) in 
                 (('GSM', '^(\+?256|0)(00)'),
                  ('MTN', '^(\+?256|0)(78|77|39)'),
                  ('UTL', '^(\+?256|0)(71)'),
                  ('Orange', '^(\+?256|0)(79)'),
                  ('Orange', '^(\+?256|0)(75)'),
                  ('Warid', '^(\+?256|0)(70)'),))

class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'useexisting' : True}

    id = Column(types.Integer, primary_key=True)
    number = Column(types.String(12), unique=True)
    name = Column(types.Unicode(50), nullable=True)
    location = Column(types.Unicode(50), nullable=True)
    mask = Column(types.Integer, default=0)

    def __unicode__(self):
        return self.name

    def __html__(self):
        for network, pattern in NETWORKS:
            if pattern.match(self.number):
                break
        else:
            network = None

        return '''
        <span class="reporter network-%s" href="#">%s</span>
        ''' % (network.lower(), self.name)

class UserHealthFacilityMembership(Base):
    __tablename__ = 'facility_memberships'

    user = Column(types.Integer, ForeignKey(User.id), primary_key=True)
    facility = Column(types.Integer)

class HealthFacility(Base):
    __tablename__ = 'facilities'

    id = Column(types.Integer, primary_key=True)
    hmis = Column(types.Integer, unique=True)
    name = Column(types.Unicode(50), nullable=True)
    location = Column(types.Unicode(50), nullable=True)
    users = relation(
        User, secondary=UserHealthFacilityMembership.__table__,
        primaryjoin=(id==UserHealthFacilityMembership.facility),
        foreign_keys=[UserHealthFacilityMembership.facility,
                      UserHealthFacilityMembership.user],
        uselist=True, backref=backref(
            'health_facility', uselist=False)
        )
