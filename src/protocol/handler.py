from webob import Response
from router.orm import Session
from router import dispatch
from . import models

class Handler(dispatch.Handler):
    _user_unknown_response = Response(
        "You have not been registered with the system. Please join first!")

    def handle_approve(self, message):
        session = Session()
        query_users = session.query(models.User)

        approver = query_users.filter_by(number=message.sender).first()
        if approver is None:
            return self._user_unknown_response

        user = query_users.filter_by(id=int(message.id)).first()
        if user is None:
            return Response(
                "Approve failed! No such user id: #%#04d." % int(message.id), status=200)

        group = models.GROUPS.get(message.group.upper())
        if group is None:
            return Response(
                "Approve failed! Group does not exist: %s." % message.group, status=200)

        permitted = group.mask & approver.mask == group.mask
        if not permitted:
            return Response(
                "Approve failed! You are not allowed to approve "
                "membership to the '%s' group." % message.group, status=200)

        user.mask |= group.mask
        session.add(user)

        # inform user of approval
        self.enqueue(
            user.number,
            "You have been approved for the %s." % group.name)

        # return feedback to approving party
        return Response(
            "You have succesfully approved %s to join the %s." % (
                user.name, group.name), status=200)

    def handle_register(self, message):
        session = Session()
        query_users = session.query(models.User)

        user = query_users.filter_by(number=message.sender).first()
        if user is not None:
            user.location = message.location
            user.name = message.name

            return Response(
                ("Hello, %(name)s (#%(id)04d). "
                 "You have updated your information.") % {
                    'name': message.name,
                    'id': user.id,
                    })

        user = models.User(
            name=message.name,
            number=message.sender,
            location=message.location)

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
