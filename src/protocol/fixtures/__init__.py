import os
import csv
import sys
import iso8601

from sqlalchemy import create_engine

from router.orm import Session
from router.orm import Base
from router.models import Message

from ..patterns import parser
from ..handler import Handler

def install_demo():
    try:
        database = sys.argv[1]
    except IndexError:
        print "Error: Must provide database connection string " \
              "(e.g. 'sqlite:///file.db')."
        sys.exit(1)

    # configure database
    db = create_engine(database)
    session = Session()
    session.configure(bind=db)
    Base.metadata.bind = db
    Base.metadata.create_all()

    queue = []
    handler = Handler(queue)

    path = os.path.join(os.path.dirname(__file__), "demo.csv")
    reader = csv.reader(open(path), delimiter='\t')
    for line in reader:
        line = filter(None, line)
        line = map(unicode, line)
        if not line:
            continue
        if line[0].strip().startswith('#'):
            continue
        try:
            sender, receiver, text, date = line
        except ValueError, e:
            print "- Skipping %s (%s)." % (repr(line), str(e))
            continue
        time = iso8601.parse_date(date)

        message = parser(text)
        message.sender = sender
        message.receiver = receiver
        message.time = time
        session.add(message)

        response = handler(message)
        print "%s >>> %s [%s]" % (sender, text, message.kind)
        print "%s <<< %s" % (sender, response.body)

    session.commit()
    print "%d messages recorded." % len(session.query(Message).all())
    session.close()
