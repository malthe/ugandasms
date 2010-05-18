import itertools

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from polymorphic import PolymorphicModel as Model
from router.models import Incoming
from router.models import User

from picoparse import remaining
from picoparse import one_of
from picoparse import optional
from picoparse import partial
from picoparse import peek
from picoparse.text import whitespace
from picoparse.text import whitespace1
from picoparse.text import caseless_string
from router.parser import one_of_strings
from router.parser import digits
from router.parser import ParseError

from polymorphic.manager import PolymorphicManager
from django.contrib.gis.db import models

class PolymorphicGeoManager(PolymorphicManager, models.GeoManager):
    pass

class Location(Model):
    name = models.CharField(max_length=50)
    coords = models.PointField(null=True)
    manager = PolymorphicGeoManager()

class Facility(Model):
    code = models.IntegerField(unique=True, primary_key=True)
    name = models.CharField(max_length=50, null=True)
    location = models.ForeignKey(Location)
    parent = models.ForeignKey("self", related_name="children", null=True)
    children = ()

class Subscription(Model):
    role = models.CharField(max_length=3)
    facility = models.ForeignKey(Facility, null=True)
    user = models.ForeignKey(User, related_name="subscriptions", null=True)

class Aggregate(Model):
    code = models.CharField(max_length=2, db_index=True)
    time = models.DateTimeField(db_index=True)
    user = models.ForeignKey(User)
    value = models.IntegerField()

    class Meta:
        ordering = ['-id']

class Epi(Incoming):
    """Report on epidemiological data.

    Regular reports should come in with the format::

      +EPI [<token> <integer_value>]*

    The ``token`` must be one of the keys defined in
    ``TOKENS``. Negative values are not allowed.

    Example input for 12 cases of malaria and 4 tuberculous cases::

      +EPI MA 12, TB 4

    The reports are confirmed in a message reply, along with
    percentage or absolute change (whichever is applicable depending
    on whether this or the previous value is zero) on consecutive
    reporting.

    Example output::

      You reported malaria 12 (+5) and tuberculosis 4 (+23%).

    All aggregates are entered into the database as separate
    objects. To group aggregates based on reports, filter by user and
    group by time.
    """

    TOKENS = {
        'BD': 'Bloody diarrhea',
        'MA': 'Malaria',
        'TB': 'Tuberculosis',
        }

    @classmethod
    def parse(cls):
        one_of('+')
        caseless_string('epi')

        aggregates = {}

        if whitespace():
            while peek():
                try:
                    code = "".join(one_of_strings(*cls.TOKENS))
                except:
                    raise ParseError(
                        "Expected an epidemiological indicator "
                        "such as TB or MA.")

                if code in aggregates:
                    raise ParseError("Duplicate value for %s." % code)

                whitespace1()
                try:
                    minus = optional(partial(one_of, '-'), '')
                    value = int("".join([minus]+digits()))
                except:
                    raise ParseError("Expected a value for %s." % code)

                if value < 0:
                    raise ParseError("Got %d for %s. You must report a positive value." % (
                        value, cls.TOKENS[code].lower()))

                aggregates[code] = value
                whitespace()

        return {
            'aggregates': aggregates
            }

    def handle(self, aggregates={}):
        if self.user is None: # pragma: NOCOVER
            self.reply(u"Please register before sending in reports.")
        elif aggregates:
            stats = []
            for code, value in sorted(aggregates.items()):
                stat = "%s %d" % (self.TOKENS[code].lower(), value)
                previous = Aggregate.objects.filter(code=code, user=self.user)
                if len(previous):
                    aggregate = previous[0]
                    if value > 0 and aggregate.value > 0:
                        ratio = 100 * (float(value)/aggregate.value - 1)
                        r = "%1.f%%" % abs(ratio)
                    else:
                        ratio = value-aggregate.value
                        r = str(abs(ratio))
                    if ratio > 0:
                        r = "+" + r
                    else:
                        r = "-" + r
                    stat += " (%s)" % r
                Aggregate(code=code, value=value, time=self.time, user=self.user).save()
                stats.append(stat)
            sep = [", "] * len(stats)
            if len(stats) > 1:
                sep[-2] = " and "
            sep[-1] = ""
            self.reply(u"You reported %s." % "".join(itertools.chain(*zip(stats, sep))))
        else:
            self.reply(u"Please include one or more reports.")

class Signup(Incoming):
    """Message to register as health worker.

    New signups use the format::

      +<token> <code>

    The token is the role name (one of ``TOKENS``), while the code is
    an integer facility code.
    """

    TOKENS = "VHT", "CHW", "HCS", "HCW"

    @classmethod
    def parse(cls):
        one_of('+')
        role = u"".join(one_of_strings(*cls.TOKENS)).upper()

        try:
            whitespace1()
            code = int(u"".join(digits()))
        except:
            raise ParseError(u"Expected an HMIS facility code (got: %s)." %
                             "".join(remaining()))

        return {
            'role': role,
            'code': code,
            }

    def handle(self, role=None, code=None):
        if self.user is None:
            self.reply(u"Please register before signing up for this service.")
        else:
            try:
                facility = Facility.objects.filter(code=code).get()
            except ObjectDoesNotExist:
                self.reply(u"No such facility code: %d." % code)
            else:
                sub = self.user.subscriptions.create(role=role, facility=facility)
                sub.save()

                self.reply((
                    "You have joined the system as %s for %s in %s. "
                    "Please resend if there is a mistake.") % (
                    getattr(settings, "HEALTH_FACILITY_ROLES", {}).get(role, role),
                    facility.name, facility.location.name))
