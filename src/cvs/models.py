import difflib

from django.conf import settings
from django.db import models

from picoparse import remaining
from picoparse import one_of
from picoparse import optional
from picoparse.text import whitespace
from picoparse.text import whitespace1

from router import pico
from router.router import FormatError
from router.models import Form
from router.models import Reporter
from router.models import ReporterRole
from location.models import Area
from location.models import Facility

class HealthRole(ReporterRole):
    keyword = models.SlugField(max_length=10)

class HealthReporter(Reporter):
    """A Reporter is someone who interacts with RapidSMS as a user of
    the system (as opposed to an administrator).

    Although not enforced, they will tend to register with the system
    via SMS.
    """

    area = models.ForeignKey(Area, null=True)
    facility = models.ForeignKey(Facility, null=True)

class Signup(Form):
    """Message to register as health worker or supervisor.

    Health workers:

      +<role> <facility_code> [, <location_name>]

    Supervisors:

      +<role> <facility_code>

    The token is the role keyword (see :class:`HealthRole`), while the
    code is an integer facility code.
    """

    @pico.wrap
    def parse(cls):
        keywords = dict((role.keyword, role) for role in HealthRole.objects.all())

        one_of('+')
        keyword = u"".join(pico.one_of_strings(*keywords)).lower()

        result = {
            'role': keywords[keyword],
            }

        try:
            whitespace1()
            code = u"".join(pico.digits())
        except:
            raise FormatError(u"Expected an HMIS facility code (got: %s)." %
                             "".join(remaining()))

        try:
            facility = result['facility'] = Facility.objects.filter(code=code).get()
        except Facility.DoesNotExist:
            raise FormatError(u"No such HMIS facility code: %d." % code)

        whitespace()

        if optional(pico.separator, None):
            name = "".join(remaining()).strip()

            # get all (name, location) pairs of all child nodes of
            # areas that report to this facility
            areas = {}
            area = None

            for area in facility.areas.all():
                areas[area.name] = area
                for descendant in area.get_descendants():
                    areas[descendant.name] = descendant

            matches = difflib.get_close_matches(name, areas)
            if matches:
                name = matches[0]
                area = areas[name]
            elif area is not None:
                new_area = area.add_child(slug="user_added_location", name=name)
                area = area.get()

                # make sure this newly created area reports to our facility
                facility.areas.add(new_area)
                area = new_area

            result['area'] = area

        return result

    def handle(self, role=None, facility=None, area=None):
        if self.reporter is None:
            self.reply(u"Please register before signing up for this service.")
        else:
            reporter, created = HealthReporter.objects.get_or_create(pk=self.reporter.pk)

            reporter.facility = facility
            reporter.area = area
            reporter.save()

            health_roles = HealthRole.objects.all()

            for role_to_check in health_roles:
                if role_to_check in health_roles:
                    reporter.roles.remove(role_to_check)

            reporter.roles.add(role)

            self.reply(
                "You have joined the system as %s reporting to %s. "
                "Please resend if there is a mistake." % (
                    getattr(settings, "HEALTH_FACILITY_ROLES", {}).get(role, role),
                    facility.name))
