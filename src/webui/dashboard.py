from router.orm import Session
from router.models import Message
from sqlalchemy.sql.expression import desc

def get_reports(limit=3):
    session = Session()
    query_messages = session.query(Message)
    return tuple(query_messages.order_by(desc(Message.time))[:limit])
