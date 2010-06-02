from django.db import models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from polymorphic import PolymorphicModel as Model
from router.models import Form
from router.models import User

from picoparse import remaining
from picoparse import one_of
from picoparse.text import whitespace1

from router import pico
from router.router import FormatError

class Location(Model):
    name = models.CharField(max_length=50)

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

class Signup(Form):
    """Message to register as health worker.

    New signups use the format::

      +<token> <code>

    The token is the role name (one of ``TOKENS``), while the code is
    an integer facility code.
    """

    TOKENS = "VHT", "CHW", "HCS", "HCW"

    @pico.wrap
    def parse(cls):
        one_of('+')
        role = u"".join(pico.one_of_strings(*cls.TOKENS)).upper()

        try:
            whitespace1()
            code = int(u"".join(pico.digits()))
        except:
            raise FormatError(u"Expected an HMIS facility code (got: %s)." %
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
