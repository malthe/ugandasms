from webob import Response
from router.orm import Session
from router import dispatch
from . import models

class Handler(dispatch.Handler):
    _user_unknown_response = Response(
        "You have not been registered with the system. Please join first!")

    def handle_registration(self, message):
        if message.user is not None:
            message.user.location = message.location
            message.user.name = message.name

            return Response(
                ("Hello, %(name)s (#%(id)04d). "
                 "You have updated your information.") % {
                    'name': message.name,
                    'id': message.user.id,
                    })

        user = models.User(
            name=message.name,
            number=message.sender,
            location=message.location)

        session = Session()
        session.add(user)
        session.flush()

        return Response(
            ("Welcome, %(name)s (#%(id)04d). "
             "You have been registered.") % {
                'name': message.name,
                'id': user.id,
                })

    def handle_not_understood(self, message):
        return Response(
            "Message not understood: %s." % message.text, status=200)
