from django.db import models

from picoparse import choice
from picoparse import commit
from picoparse import many1
from picoparse import not_one_of
from picoparse import one_of
from picoparse import optional
from picoparse import partial
from picoparse import tri
from picoparse.text import whitespace1

from router.pico import one_of_strings
from router.pico import wrap as pico
from router.models import Form
from router.models import Peer
from router.models import User

class Reporter(User):
    name = models.CharField(max_length=50)

class Registration(Form):
    """Register with the system.

    New users will register using the format::

       +REG[ISTER] <name>

    At any time, this registration may be updated (change name).

    Users may add a device or handset to their user account by
    providing the identification string (usually a phone number)::

       +REG[ISTER] #<ident>

    To query for the identification string of the current device::

       +REG[ISTER]
    """

    @pico
    def parse(cls):
        one_of('+')
        one_of_strings('register', 'reg')

        result = {}

        @tri
        def ident():
            whitespace1()
            one_of('#')
            commit()
            result['ident'] = "".join(many1(partial(not_one_of, ',')))

        @tri
        def name():
            whitespace1()
            result['name'] = "".join(many1(partial(not_one_of, ',')))

        optional(partial(choice, ident, name), None)
        return result

    def handle(self, name=None, ident=None):
        if self.user is None:
            if ident is not None:
                # identify user using ``ident`` and add this peer
                peer = Peer.objects.get(uri__endswith="://%s" % ident)
                if peer.user is None:
                    self.reply("We did not find an existing registration "
                               "identified by: %s." % ident)
                else:
                    peer.user.peers.add(self.message.peer)
                    self.message.peer.save()
                    self.reply("Thank you for your registration.")
            elif name is not None:
                user = Reporter(name=name)
                user.save()
                self.message.peer.user = user
                self.message.peer.save()

                self.reply((
                    "Welcome, %(name)s. "
                    "You have been registered.") % {
                    'name': name,
                    })
            else:
                self.reply("Please provide your name when registering.")
        else:
            if name is None:
                self.reply("You're currently registered with %s." % \
                           self.message.ident)
            else:
                self.user.name = name
                self.user.save()

                self.reply((
                    "Hello, %(name)s. "
                    "You have updated your information.") % {
                        'name': name,
                    })
