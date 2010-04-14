import logging
import threading

from Queue import Queue, Empty
from sqlalchemy import create_engine

from router.run import WSGIApp
from router.box import Connection
from router.orm import Session
from router.orm import Base

from .patterns import parser
from .handler import Handler

def send_loop(queue, connection, owner):
    while True:
        try:
            message = queue.get(True, 1.0)
        except Empty:
            # we have to garbage collect at regular intervals to
            # make sure thread finishes when router application
            # comes out of scope
            if owner.is_alive():
                continue
            else:
                logging.info("Queue stopped.")
                return

        try:
            result = connection.send(
                message.sender, message.receiver, message.text)
            message.state = result
        finally:
            queue.task_done()

def make_router(config, database="sqlite://",
                host="localhost", port="13013", username=None, password=None):
    # configure database
    db = create_engine(database)
    session = Session()
    session.configure(bind=db)
    Base.metadata.bind = db
    Base.metadata.create_all()

    # configure router
    queue = Queue()
    handler = Handler(queue)
    router = WSGIApp(parser, handler)

    # configure send thread
    connection = Connection(host, int(port), username, password)
    owner = threading.current_thread()
    thread = threading.Thread(target=send_loop, args=(queue, connection, owner))
    thread.start()

    return router
