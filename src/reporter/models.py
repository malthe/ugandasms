import re
import string

from picoparse import any_token
from picoparse import choice
from picoparse import commit
from picoparse import many1
from picoparse import one_of
from picoparse import optional
from picoparse import partial
from picoparse import tri
from picoparse.text import whitespace1

from router import pico
from router.models import Form
from router.models import Connection
from router.models import Reporter

from stats.models import Report

class Registration(Form):
    """Register with the system.

    New users will register using the format::

       +REG[ISTER] <name>

    At any time, this registration may be updated (change name).

    Users may add a device or handset to their user account by
    providing the identification string (usually a phone number)::

       +REG[ISTER] <phone number>
       +REG[ISTER] #<ident>

    Note that if a phone number is provided, the hash character
    ``\"#\"`` can be omitted.

    To query for the number of the current device::

       +REG[ISTER]
    """

    prompt = "REGISTER: "

    @pico.wrap
    def parse(cls):
        one_of('+')
        pico.one_of_strings('register', 'reg')

        result = {}

        @tri
        def ident():
            whitespace1()
            pico.hash()
            commit()
            return many1(any_token)

        @tri
        def number():
            whitespace1()
            return many1(partial(one_of, string.digits + ' -+()'))

        @tri
        def name():
            whitespace1()
            return pico.name()

        ident = optional(partial(choice, ident, number), None)
        if ident is not None:
            result['ident'] = re.sub('[ \-+()]', '', "".join(ident))
        else:
            name = optional(name, None)
            if name is not None:
                result['name'] = name

        return result

    def handle(self, name=None, ident=None):
        if self.reporter is None:
            if ident is not None:
                # identify user using ``ident`` and add this connection
                connection = Connection.objects.get(uri__endswith="://%s" % ident)
                if connection.reporter is None:
                    self.reply("We did not find an existing registration "
                               "identified by: %s." % ident)
                else:
                    connection.reporter.connections.add(self.message.connection)
                    self.message.connection.save()
                    self.reply("Thank you for your registration.")
            elif name is not None:
                reporter = Reporter(name=name)
                reporter.save()
                self.message.connection.reporter = reporter
                self.message.connection.save()

                Report.from_observations(
                    "registration", source=self, location=None,
                    new_user=1)

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
                           self.message.connection.ident)
            else:
                self.reporter.name = name
                self.reporter.save()

                self.reply((
                    "Hello, %(name)s. "
                    "You have updated your information.") % {
                        'name': name,
                    })
