import os
import csv
import sys
import iso8601

from sqlalchemy import create_engine

from router.orm import Session
from router.orm import Base

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
        if not line:
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

        print "%s >>> %s" % (sender, text)
        response = handler(message)
        print "%s <<< %s" % (sender, response.body)

