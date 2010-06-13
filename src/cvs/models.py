import difflib

from django.db import models
from django.db.models import signals

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
from stats.models import Report

def on_save_report(sender=None, instance=None, **kwargs):
    if not issubclass(sender, Report):
        return

    if instance.source is None:
        return

    reporter = instance.source.reporter
    if reporter is None:
        return

    try:
        reporter = HealthReporter.objects.get(pk=reporter.pk)
    except HealthReporter.DoesNotExist:
        return

    if instance.location is not None or reporter.area is None:
        return

    instance.location = reporter.area
    instance.save()

signals.post_save.connect(on_save_report, weak=True)

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
        whitespace()
        keyword = u"".join(pico.one_of_strings(*keywords)).upper()

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
            raise FormatError(u"No such HMIS facility code: %s." % code)

        whitespace()
        optional(pico.separator, None)

        # optionally provide a sub-village area
        name = "".join(remaining()).strip()
        if name:
            # get all (name, location) pairs of all child nodes of
            # areas that report to this facility
            areas = {}
            area = None

            for area in facility.areas.all():
                areas[area.name.upper()] = area
                for descendant in area.get_descendants():
                    areas[descendant.name.upper()] = descendant

            matches = difflib.get_close_matches(name.upper(), areas)
            if matches:
                name = matches[0]
                area = areas[name]
            elif area is not None:
                new_area = area.add_child(
                    slug="user_added_location", name='"%s"' % name)
                area = area.get()

                # make sure this newly created area reports to our facility
                facility.areas.add(new_area)
                area = new_area

            result['area'] = area

        return result

    def handle(self, role=None, facility=None, area=None):
        reporter = self.reporter
        if reporter is None:
            self.reply(u"Please register before signing up for this service.")
        else:
            try:
                reporter = HealthReporter.objects.get(pk=reporter.pk)
            except HealthReporter.DoesNotExist:
                reporter = HealthReporter(pk=reporter.pk, name=reporter.name)

            reporter.facility = facility
            reporter.area = area
            reporter.save()

            health_roles = HealthRole.objects.all()

            for role_to_check in health_roles:
                if role_to_check in health_roles:
                    reporter.roles.remove(role_to_check)

            reporter.roles.add(role)

            if area is not None:
                self.reply(
                    "You have joined the system as %s reporting to %s in %s. "
                    "Please resend if there is a mistake." % (
                        role.name, facility.name, area.name))
            else:
                self.reply(
                    "You have joined the system as %s reporting to %s. "
                    "Please resend if there is a mistake." % (
                        role.name, facility.name))
