from django.db import models

from picoparse import choice
from picoparse import commit
from picoparse import eof
from picoparse import many1
from picoparse import not_one_of
from picoparse import one_of
from picoparse import optional
from picoparse import partial
from picoparse.text import whitespace1

from router.parser import digits
from router.parser import one_of_strings
from router.parser import ParseError
from router.models import Incoming
from router.models import User

class Reporter(User):
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

class Registration(Incoming):
    """Register with the system.

    New users will register using the format::

       +REG[ISTER] <name>

    At any time, this registration may be updated (change name).

    The user registration carries an integer user id number which is
    printed in the registration reply. Existing users may inquire for
    this number at any time using an empty query::

       +REG[ISTER]

    To register another device for the same user account, provide the
    user id number::

       +REG[ISTER] [#]<user_id>

    The hash (``"#"``) prefix is optional.
    """

    name = models.CharField(max_length=50, null=True)
    user_id = models.IntegerField(null=True)

    @staticmethod
    def parse():
        one_of('+')
        one_of_strings('register', 'reg')
        choice(whitespace1, eof)

        def prefixed_digits():
            one_of('#')
            commit()
            return digits()

        try:
            user_id = optional(partial(choice, prefixed_digits, digits), None)
        except:
            raise ParseError(u"Please provide a user id number.")

        if user_id is None:
            chars = optional(partial(many1, partial(not_one_of, ',')), None)
            if chars is not None:
                return {
                    'name': "".join(chars),
                    }
            return None

        return {
            'user_id': int("".join(user_id))
            }

    def handle(self):
        if self.user is None:
            if self.user_id is not None:
                # add this peer to the referenced user
                try:
                    self.user = Reporter.objects.get(pk=self.user_id)
                except User.objects.DoesNotExist:
                    self.reply("We could not find a reporter with "
                               "the id #%04d." % self.user_id)
                else:
                    self.user.peers.add(self.peer)
                    self.user.save()
            elif self.name is not None:
                user = Reporter(name=self.name)
                user.save()
                self.peer.user = user
                self.peer.save()

                self.reply((
                    "Welcome, %(name)s (#%(id)04d). "
                    "You have been registered.") % {
                    'name': self.name,
                    'id': self.user.id,
                    })
            else:
                self.reply("Please provide your name when registering.")
        else:
            self.user, created = Reporter.objects.get_or_create(pk=self.user.pk)

            if self.name is None:
                self.reply("Your user id is #%04d." % self.user.id)
            else:
                self.user.name = self.name
                self.user.save()

                self.reply((
                    "Hello, %(name)s (#%(id)04d). "
                    "You have updated your information.") % {
                               'name': self.name,
                               'id': self.user.id,
                               })
