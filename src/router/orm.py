import re

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import DeclarativeMeta

def camelcase_to_underscore(str):
    return re.sub(
        '(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '-\\1',
        str).lower().strip('-')

class PolymorphicMeta(DeclarativeMeta):
    def __new__(meta, name, bases, attrs):
        kind = camelcase_to_underscore(name)
        attrs = attrs.copy()
        args = attrs.setdefault('__mapper_args__', {})
        args['polymorphic_identity'] = kind
        return type.__new__(meta, name, bases, attrs)

Session = scoped_session(sessionmaker(autoflush=False))
Base = declarative_base(metaclass=PolymorphicMeta)

