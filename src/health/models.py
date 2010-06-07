import itertools
import datetime
import random
import difflib

from django.db import models
from django.db import IntegrityError
from django.db.models import Model
from django.conf import settings

from picoparse import any_token
from picoparse import choice
from picoparse import many
from picoparse import many1
from picoparse import many_until
from picoparse import one_of
from picoparse import optional
from picoparse import partial
from picoparse import peek
from picoparse import remaining
from picoparse import tri
from picoparse.text import whitespace
from picoparse.text import whitespace1
from picoparse.text import caseless_string

from router import pico
from router.models import Form
from router.models import Reporter
from router.router import FormatError

from stats.models import Observation
from stats.models import ObservationKind
from stats.models import Report
from stats.models import ReportKind

date = partial(pico.date, formats=settings.DATE_INPUT_FORMATS)

TRACKING_ID_LETTERS = tuple('ABCDEFGHJKLMPQRTUVXZ')

GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
    )

BIRTH_PLACE_CHOICES = (
    ('HOME', 'Home'),
    ('CLINIC', 'Clinic'),
    ('FACILITY', 'Facility'),
    )

def generate_tracking_id():
    return '%2.d%s%s%2.d' % (
        random.randint(0, 99),
        random.choice(TRACKING_ID_LETTERS),
        random.choice(TRACKING_ID_LETTERS),
        random.randint(0, 99))

def parse_patient_input():
    result = {}

    try:
        whitespace1()

        identifiers = optional(tri(pico.ids), None)
        if identifiers:
            result['ids'] = [id.upper() for id in identifiers]
        else:
            result['name'] = pico.name()
    except:
        raise FormatError(
            "Expected a name, or a patient's health or tracking ID "
            "(got: %s)." % "".join(remaining()))

    if 'name' in result:
        try:
            many1(partial(one_of, ' ,;'))
            result['sex'] = pico.one_of_strings(
                'male', 'female', 'm', 'f')[0].upper()
        except:
            raise FormatError(
                "Expected the infant's gender "
                "(\"male\", \"female\", or simply \"m\" or \"f\"), "
                "but received instead: %s." % "".join(remaining()))
        try:
            pico.separator()
        except:
            raise FormatError("Expected age or birthdate of patient.")

        try:
            result['age'] = choice(*map(tri, (pico.date, pico.timedelta)))
        except:
            raise FormatError("Expected age or birthdate of patient, but "
                             "received %s." % "".join(remaining()))

    return result

class Patient(Model):
    health_id = models.CharField(max_length=30, null=True)
    name = models.CharField(max_length=50)
    sex = models.CharField(max_length=1, choices=GENDER_CHOICES)
    birthdate = models.DateTimeField()
    deathdate = models.DateTimeField(null=True)
    last_reported_on_by = models.ForeignKey(Reporter)

    @property
    def age(self):
        if self.birthdate is not None:
            return datetime.datetime.now() - self.birthdate

    @property
    def label(self):
        noun = 'male' if self.sex == 'M' else 'female'

        days = self.age.days

        if days > 365:
            age_string = "aged %d" % (days // 365)
        elif days > 30:
            age_string = "(%d months old)" % (days // 30)
        else:
            age_string = "(infant)"

        return "%s, %s %s" % (self.name, noun, age_string)

    @classmethod
    def identify(cls, name, sex, birthdate, reporter):
        patients = Patient.objects.filter(
            last_reported_on_by=reporter,
            name__icontains=name).all()

        names = [patient.name for patient in patients]
        matches = difflib.get_close_matches(name, names)
        if not matches:
            return

        name = matches[0]

        # return first match
        for patient in patients:
            if patient.name == name:
                return patient

class Tag(Model):
    report = models.ForeignKey(Report, related_name="tags")
    value = models.CharField(max_length=20)

class Case(Model):
    """Attached to a report that needs tracking."""

    patient = models.ForeignKey(Patient, related_name="cases")
    report = models.ForeignKey(Report, related_name="cases")
    tracking_id = models.CharField(max_length=20, unique=True)
    closed = models.DateTimeField(null=True)

class BirthReport(Report):
    patient = models.ForeignKey(Patient)
    place = models.CharField(max_length=25, choices=BIRTH_PLACE_CHOICES)

class NutritionReport(Report):
    patient = models.ForeignKey(Patient)
    category = models.CharField(max_length=1)
    reading = models.FloatField(null=True)
    oedema = models.BooleanField()

class BirthForm(Form):
    """Report a birth.

    Note that although this is not a complete birth registration form,
    we still enter a new patient record.

    Format::

      +BIRTH <name>, <sex> <location>

    We include ``name`` to corroborate the data. Location can one of:

    * At Home -- ``\"home\"``
    * Clinic -- ``\"clinic\"``
    * Health Facility -- ``\"facility\"``

    The last part of the form is forgiving in the sense that it just
    checks if any of these words occur in the remaining part of the
    message (until a punctuation).
    """

    prompt = "Birth: "

    @pico.wrap
    def parse(cls):
        one_of('+')
        caseless_string('birth')

        result = {}

        try:
            whitespace1()
            result['name'] = pico.name()
        except:
            raise FormatError(
                "Expected name (got: %s)." % "".join(remaining()))

        try:
            many1(partial(one_of, ' ,;'))
            result['sex'] = pico.one_of_strings(
                'male', 'female', 'm', 'f')[0].upper()
        except:
            raise FormatError(
                "Expected the infant's gender "
                "(\"male\", \"female\", or simply \"m\" or \"f\"), "
                "but received instead: %s." % "".join(remaining()))

        try:
            many1(partial(one_of, ' ,;'))
            words = pico.name().lower()
        except:
            raise FormatError(
                "Expected a location; "
                "either \"home\", \"clinic\" or \"facility\" "
                "(got: %s)." % "".join(remaining()))

        for word in words.split():
            matches = difflib.get_close_matches(
                word, ('home', 'clinic', 'facility'))
            if matches:
                result['place'] = matches[0].upper()
                break
        else:
            raise FormatError(
                "Did not understand the location: %s." % words)

        return result

    def handle(self, name=None, sex=None, place=None):
        if self.reporter is None: # pragma: NOCOVER
            return self.reply(u"Please register before sending in reports.")

        birthdate = datetime.datetime.now()

        patient = Patient(
            name=name, sex=sex, birthdate=birthdate,
            last_reported_on_by=self.reporter)
        patient.save()

        observations = {
            'male' if sex == 'M' else 'female': 1,
            "birth_at_%s" % place.lower(): 1
            }

        Report.from_observations(
            "birth", source=self, location=None, **observations)

        birth = BirthReport(slug="birth", patient=patient, place=place, source=self)
        birth.save()

        self.reply("Thank you for registering the birth of %s." % \
                   patient.label)

class PatientVisitationForm(Form):
    report_kind = None

    def handle(self, ids=None, name=None, sex=None, age=None):
        if self.reporter is None: # pragma: NOCOVER
            return self.reply(u"Please register before sending in reports.")

        if ids is not None:
            # this may be a tracking ids or a health ids; try both.
            cases = set(Case.objects.filter(tracking_id__in=ids).all())
            patients = set(Patient.objects.filter(health_id__in=ids).all())

            found = set([case.tracking_id for case in cases]) | \
                    set([case.health_id for case in patients])

            not_found = set(ids) - found

            if not_found:
                return self.reply(
                    "The id(s) %s do not exist. "
                    "Please correct and resend all."  % \
                    ", ".join(not_found))

            patients |= set(case.patient for case in cases)
            cases |= set(itertools.chain(*[
                patient.cases.all() for patient in patients]))

        else:
            if isinstance(age, datetime.timedelta):
                birthdate = datetime.datetime.now() - age
            else:
                birthdate = age

            patient = Patient.identify(name, sex, birthdate, self.reporter)
            if patient is None:
                Report.from_observations(slug=self.report_kind, unregistered_patient=1)
                return self.handle_unregistered(name, sex, age)

            cases = patient.cases.all()
            patients = [patient]

        notifications = {}
        for case in cases:
            # check if we need to notify the original case reporter
            assert case.report.source is not None
            case_reporter = case.report.source.reporter
            if  case_reporter != self.reporter:
                notifications[case_reporter.pk] = case.patient

        Report.from_observations(slug=self.report_kind, registered_patient=len(patients))
        self.handle_registered(patients, cases, notifications)

class DeathForm(PatientVisitationForm):
    """Report a death.

    Format::

      +DEATH <name>, <sex>, <age>
      +DEATH [<health_id>]+
      +DEATH [<tracking_id>]+

    """

    prompt = "Death: "
    report_kind = "death"

    @pico.wrap
    def parse(cls):
        one_of('+')
        caseless_string('death')
        return parse_patient_input()

    def handle_unregistered(self, name, sex, age):
        return self.reply(
            u"We have recorded the death of %s." % name)

    def handle_registered(self, patients, cases, notifications):
        for patient in patients:
            patient.deathdate = self.message.time
            patient.save()

        for case in cases:
            case.closed = self.message.time
            case.save()

        Report.from_observations(slug=self.report_kind, closing_of_case=len(cases))

        for pk, patient in notifications.items():
            reporter = Reporter.objects.get(pk=pk)
            self.reply(
                u"This is to inform you that "
                "Your patient, %s, has died." % patient.label,
                reporter=reporter)

        self.reply(
            "Thank you for reporting the death of %s; "
            "we have closed %d open case(s)." % (
                ", ".join(patient.label for patient in patients),
                len(cases)))

class CureForm(PatientVisitationForm):
    """Mark a case as closed due to curing.

    Format::

      +CURE [<tracking_id>]+

    Separate multiple entries with space and/or comma. Tracking IDs
    are case-insensitive.
    """

    prompt = "Cured: "
    report_kind = "cure"

    @pico.wrap
    def parse(cls):
        one_of('+')
        caseless_string('cure')
        return parse_patient_input()

    def handle_unregistered(self, name, sex, age):
        return self.reply(
            u"We have recorded the curing of %s." % name)

    def handle_registered(self, patients, cases, notifications):
        for case in cases:
            case.closed = self.message.time
            case.save()

        Report.from_observations(slug=self.report_kind, closing_of_case=len(cases))

        for pk, patient in notifications.items():
            reporter = Reporter.objects.get(pk=pk)
            self.reply(
                u"This is to inform you that "
                "Your patient, %s, has been cured." % patient.label,
                reporter=reporter)

        self.reply(
            "Thank you for reporting the curing of %s; "
            "we have closed %d open case(s)." % (
                ", ".join(patient.label for patient in patients),
                len(cases)))

class OtpForm(PatientVisitationForm):
    """Mark a case as seen in outpatient therapeutic program care.

    Format::

      +OTP [<tracking_id>]+

    Separate multiple entries with space and/or comma. Tracking IDs
    are case-insensitive.
    """

    prompt = "OTP: "
    report_kind = "otp"

    @pico.wrap
    def parse(cls):
        one_of('+')
        caseless_string('otp')
        return parse_patient_input()

    def handle_unregistered(self, name, sex, age):
        return self.reply(
            u"We have recorded the OTP visit of %s." % name)

    def handle_registered(self, patients, cases, notifications):
        for pk, patient in notifications.items():
            reporter = Reporter.objects.get(pk=pk)
            self.reply(
                u"This is to inform you that "
                "Your patient, %s, has received OTP treatment." % patient.label,
                reporter=reporter)

        self.reply(
            "Thank you for reporting the OTP treatment of %s." % \
            ", ".join(patient.label for patient in patients))

class ObservationForm(Form):
    """Form to allow multiple observation input.

    This form supports the following observation groups:

    * Epidemiology
    * Domestic Health

    For flexible use, multiple command strings are accepted::

      +EPI
      +HOME

    Regular reports should come in with the format::

      [<total>, ]? [<code> <integer_value>]*

    For each entry, the value for ``code`` must map (via the command
    string) to an observation kind, e.g. for an epidemiological report
    on malaria, ``\"MA\"`` would map to the observation kind
    ``\"epi_ma\"``.

    Only decimal values allowed; negative values are disallowed.

    Example input for 12 cases of malaria and 4 tuberculous cases::

      +EPI MA 12, TB 4

    The reports are confirmed in the reply, along with percentage or
    absolute change (whichever is applicable depending on whether this
    or the previous value is zero) on consecutive reporting.

    Example output::

      You reported malaria 12 (+5) and tuberculosis 4 (+23%).

    All aggregates are entered into the database as separate
    objects. To group aggregates based on reports, filter by reporter
    and group by time.
    """

    ALIASES = {
        'epi_dy': 'epi_bd',
        }

    COMMANDS = {
        'epi': 'epidemiological_observations',
        'home': 'observations_at_home',
        }

    prompt = "Report: "

    @pico.wrap
    def parse(cls, commands=None):
        if commands is None:
            commands = cls.COMMANDS

        one_of('+')
        command = "".join(pico.one_of_strings(*commands))
        slug = commands[command]
        kind = ReportKind.objects.get(slug=slug)

        observations = {}
        result = {
            'observations': observations,
            'kind': kind,
            }

        if whitespace():
            total = "".join(optional(pico.digits, ()))
            if total:
                result['total'] = int(total)
                many1(partial(one_of, ' ,;'))

            kinds = ObservationKind.objects.filter(slug__startswith="%s_" % slug).all()
            observation_kinds = dict((kind.slug, kind) for kind in kinds)
            codes = [observation_slug.split('_', 1)[1]
                     for observation_slug in observation_kinds]

            # we allow both the observation kinds and any aliases
            allowed_codes = tuple(codes) + tuple(cls.ALIASES)

            while peek():
                # look up observation kinds that double as user input
                # for the aggregate codes
                try:
                    code = "".join(pico.one_of_strings(*allowed_codes)).lower()
                except:
                    raise FormatError(
                        "Expected an indicator code "
                        "such as TB or MA (got: %s)." % \
                        "".join(remaining()))

                # rewrite alias if required, then look up kind
                munged= "%s_%s" % (slug, code)
                munged = cls.ALIASES.get(munged, munged)
                kind = observation_kinds[munged]

                # guard against duplicate entries
                if kind.slug in observations:
                    raise FormatError("Duplicate value for %s." % code)

                whitespace()

                try:
                    minus = optional(partial(one_of, '-'), '')
                    value = int("".join([minus]+pico.digits()))
                except:
                    raise FormatError("Expected a value for %s." % code)

                if value < 0:
                    raise FormatError("Got %d for %s. You must "
                                      "report a positive value." % (
                        value, kind.name))

                observations[kind.slug] = value
                many(partial(one_of, ' ,;.'))

        return result

    def handle(self, kind=None, total=None, observations={}):
        if self.reporter is None: # pragma: NOCOVER
            self.reply(u"Please register before sending in reports.")
        elif observations:
            # determine whether there's any previous reports for this user
            previous_reports = Report.objects.filter(
                kind=kind, source__message__connection__reporter=self.reporter).all()
            if previous_reports:
                previous = previous_reports[0]
            else:
                previous = None

            # create new report to contain these observations
            report = Report(kind=kind, source=self)
            report.save()

            # we keep running tally of stats to generate message reply
            # item by item
            stats = []

            for slug, value in sorted(observations.items()):
                kind = ObservationKind.objects.get(slug=slug)
                stat = "%s %d" % (kind.name.lower(), value)

                previous_value = None
                if previous is not None:
                    try:
                        previous_observation = previous.observations.get(kind=kind)
                    except Observation.DoesNotExist: # pragma: NOCOVER
                        pass
                    else:
                        previous_value = previous_observation.value

                if previous_value is not None:
                    if value > 0 and previous_value > 0:
                        ratio = 100 * (float(value)/float(previous_value) - 1)
                        r = "%1.f%%" % abs(ratio)
                    else:
                        ratio = value-int(previous_value)
                        r = str(abs(ratio))
                    if ratio > 0:
                        r = "+" + r
                    else:
                        r = "-" + r
                    stat += " (%s)" % r

                report.observations.create(kind=kind, value=value)
                stats.append(stat)

            if total is not None:
                report.observations.create(slug="total", value=total)

            separator = [", "] * len(stats)
            if len(stats) > 1:
                separator[-2] = " and "
            separator[-1] = ""

            self.reply(u"You reported %s." % "".join(
                itertools.chain(*zip(stats, separator))))
        else:
            self.reply(u"Please include one or more reports.")

class MuacForm(Form):
    """Middle upper arm circumference measurement.

    Formats::

      +MUAC <name>, <sex>, <age>, <reading> [,oedema]
      +MUAC <health_id>, <reading> [,oedema]
      <health_id> +MUAC <reading> [,oedema]

    Note that a patient id must contain one or more digits (to
    distinguish a name from a patient id).

    Oedema may be specified as \"oedema\" or simply \"oe\".

    Reading is one of (case-insensitive):

    - ``\"red\"`` (or ``\"r\"``)
    - ``\"yellow\"`` (or ``\"y\"``)
    - ``\"green\"`` (or ``\"g\"``)

    Or, alternatively the reading may be a floating point number,
    e.g. ``\"114 mm\"`` (unit optional).
    values > 30, otherwise *cm* is assumed). While such a value will
    be translated into one of the readings above, the given number is
    still recorded.

    Both yellow and red categories result in a referral. Included in
    the reply is then a tracking ID which is used in other commands to
    follow up on the referral.
    """

    prompt = "MUAC: "

    @staticmethod
    def get_reading_in_mm(reading):
        if reading > 30:
            return reading
        return reading*10

    @pico.wrap
    def parse(self):
        result = {}

        prefix = optional(tri(pico.identifier), None)
        if prefix is not None:
            result['health_id'] = "".join(prefix)
            whitespace()

        one_of('+')
        caseless_string('muac')

        if prefix is None:
            try:
                whitespace1()
                part = optional(tri(pico.identifier), None)
                if part is not None:
                    result['health_id'] = "".join(part)
                else:
                    result['name'] = pico.name()
            except:
                raise FormatError("Expected a patient id or name.")

        if 'name' in result:
            try:
                pico.separator()
                result['sex'] = one_of('MmFf').upper()
            except:
                raise FormatError("Expected either M or F "
                                  "to indicate the patient's gender.")

            try:
                pico.separator()
            except:
                raise FormatError("Expected age or birthdate of patient.")

            try:
                result['age'] = choice(*map(tri, (pico.date, pico.timedelta)))
            except:
                received, stop = many_until(any_token, pico.comma)
                raise FormatError("Expected age or birthdate of patient, but "
                                 "received %s." % "".join(received))
        try:
            if prefix is None:
                pico.separator()
            else:
                whitespace1()

            reading = choice(
                partial(pico.one_of_strings,
                        'red', 'green', 'yellow', 'r', 'g', 'y'), pico.digits)

            try:
                reading = int("".join(reading))
            except:
                result['category'] = reading[0].upper()
            else:
                whitespace()
                unit = optional(partial(pico.one_of_strings, 'mm', 'cm'), None)
                if unit is None:
                    reading = self.get_reading_in_mm(reading)
                elif "".join(unit) == 'cm':
                    reading = reading * 10
                result['reading'] = reading
        except:
            raise FormatError(
                "Expected MUAC reading (either green, yellow or red), but "
                "received %s." % "".join(remaining()))

        if optional(pico.separator, None):
            try:
                oedema = pico.one_of_strings('oedema', 'oe')
                result['oedema'] = bool(oedema)
            except:
                raise FormatError(
                    "Specify \"oedema\"  or \"oe\" if the patient shows "
                    "signs of oedema, otherwise leave empty.")

        return result

    def handle(self, health_id=None, name=None, sex=None,
               age=None, category=None, reading=None, oedema=False):

        if self.reporter is None: # pragma: NOCOVER
            return self.reply(u"Please register before sending in reports.")

        if health_id is None:
            if isinstance(age, datetime.timedelta):
                birthdate = datetime.datetime.now() - age
            else:
                birthdate = age

            # attempt to identify the patient using the information
            patient = Patient.identify(name, sex, birthdate, self.reporter)

            # if we fail to identify the patient, we create a new record
            if patient is None:
                patient = Patient(
                    name=name, sex=sex, birthdate=birthdate,
                    last_reported_on_by=self.reporter)
                patient.save()
        else:
            try:
                patient = Patient.objects.filter(health_id=health_id).get()
            except Patient.DoesNotExist:
                return self.reply(u"Patient not found: %s." % health_id)

        if category is None and reading is not None:
            if reading > 125:
                category = 'G'
            elif reading < 114:
                category = 'R'
            else:
                category = 'Y'

        report = NutritionReport(
            slug="nutrition",
            reading=reading,
            category=category,
            patient=patient,
            oedema=oedema)

        report.save()

        report.observations.create(slug="oedema", value=int(oedema))
        report.observations.create(
            slug="age_in_days",
            value=(datetime.datetime.now()-patient.birthdate).days)
        report.observations.create(
            slug={'G': 'green_muac', 'Y': 'yellow_muac', 'R': 'red_muac'}[category],
            value=1)

        pronoun = 'his' if patient.sex == 'M' else 'her'

        if category != 'G' or oedema:
            case = Case(patient=patient, report=report)
            while case.id is None:
                try:
                    tracking_id = generate_tracking_id()
                    case.tracking_id = tracking_id
                    case.save()
                except IntegrityError: # pragma: NOCOVER
                    pass

            Report.from_observations(slug="nutrition", opening_of_case=1)

            if category == 'Y':
                severity = "Risk of"
            else:
                severity = "Severe Acute"

            if oedema:
                possibly_oedema = "(with oedema)"
            else:
                possibly_oedema = ""

            self.reply(
                "%s has been identified with "
                "%s Malnutrition%s. %s Case Number %s." % (
                patient.label, severity, possibly_oedema, pronoun.capitalize(),
                    tracking_id))
        else:
            self.reply(
                "Thank you for reporting your measurement of "
                "%s. %s reading is normal (green)." % (
                    patient.label, pronoun.capitalize()))
