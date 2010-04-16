from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.ext.declarative import declarative_base

Session = scoped_session(sessionmaker(autoflush=False))
Base = declarative_base()

