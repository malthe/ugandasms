from router.models import Message

class Empty(Message):
    """The empty message."""

class Register(Message):
    """Register with the system."""

class Approve(Message):
    """Approve user to join group."""
