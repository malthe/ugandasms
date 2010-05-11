from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from router.models import Incoming
from router.models import User

from picoparse import any_token
from picoparse import many
from picoparse import not_one_of
from picoparse import one_of
from picoparse import optional
from picoparse import partial
from picoparse import remaining
from picoparse.text import whitespace1
from router.parser import one_of_strings
from router.parser import next_parameter
from router.parser import ParseError

class Registration(Incoming):
    """Register with the system."""

    name = models.CharField(max_length=50, null=True)
    location = models.CharField(max_length=50, null=True)

    @staticmethod
    def parse():
        one_of('+')
        one_of_strings('register', 'reg')
        try:
            whitespace1()
            name = u"".join(many(partial(not_one_of, ',')))
        except:
            raise ParseError(u"Must provide a name (got: %s)." % "".join(remaining()))

        location = optional(partial(next_parameter, parser=any_token), None)

        return {
            'name': name,
            'location': location,
            }

    def handle(self):
        if self.user is None:
            self.user = User(
                name = self.name,
                location = self.location
                )

            self.user.save()

            # we define the relation to the message per only after the
            # user object has been saved (to ensure that we have a
            # primary key)
            self.user.peers.add(self.peer)
            self.user.save()

            return (
                "Welcome, %(name)s (#%(id)04d). "
                "You have been registered.") % {
                'name': self.name,
                'id': self.user.id,
                }

        self.user.name = self.name
        self.user.location = self.location
        self.user.save()

        return (
            "Hello, %(name)s (#%(id)04d). "
            "You have updated your information.") % {
            'name': self.name,
            'id': self.user.id,
            }
