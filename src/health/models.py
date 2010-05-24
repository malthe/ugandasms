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
from router.models import User
from router.router import FormatError

date = partial(pico.date, formats=settings.DATE_INPUT_FORMATS)

TRACKING_ID_LETTERS = ['ABCDEFGHJKLMPQRTUVXZ']

def generate_tracking_id():
    return '%2.d%s%s%2.d' % (
        random.randint(0, 99),
        random.choice(TRACKING_ID_LETTERS),
        random.choice(TRACKING_ID_LETTERS),
        random.randint(0, 99))

class Patient(Model):
    health_id = models.CharField(max_length=30)
    name = models.CharField(max_length=50)
    sex = models.CharField(max_length=1)
    birthdate = models.DateTimeField()
    last_reported_on_by = models.ForeignKey(User)

    @property
    def age(self):
        if self.birthdate is not None:
            return datetime.datetime.now() - self.birthdate

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

class Report(Model):
    """Report sent in by reporting staff, possibly tagged with one or
    more keywords."""

    reporter = models.ForeignKey(User)
    time = models.DateTimeField(db_index=True)
    tags = ()

    class Meta:
        ordering = ['-id']

class Tag(Model):
    report = models.ForeignKey(Report, related_name="tags")
    value = models.CharField(max_length=20)

class Case(Model):
    """Attached to a report when it needs tracking."""

    patient = models.ForeignKey(Patient, related_name="cases")
    report = models.ForeignKey(Report, related_name="cases")
    tracking_id = models.CharField(max_length=20, unique=True)

class Aggregate(Report):
    """An aggregate occurrence report codified by a two-letter
    keyword."""

    code = models.CharField(max_length=2, db_index=True)
    value = models.IntegerField()

class MuacMeasurement(Report):
    """Measurement record of the MUAC heuristic."""

    category = models.CharField(max_length=1)
    reading = models.FloatField(null=True)
    patient = models.ForeignKey(Patient, null=True)

class Epi(Form):
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
        'AB': 'Animal Bites',
        'AF': 'Acute Flaccid Paralysis (Polio)',
        'MG': 'Meningitis',
        'ME': 'Measles',
        'BD': 'Bloody Diarrhea (Dysentery)',
        'CH': 'Cholera',
        'GW': 'Guinea Worm',
        'NT': 'Neonatal Tetanus',
        'YF': 'Yellow Fever',
        'OT': 'Other',
        'PL': 'Plague',
        'RB': 'Rabies',
        'VF': 'Other Viral Hemorrhagic Fevers',
        'EI': 'Other Emerging Infectious Diseases',
        }

    ALIAS = {
        'DY': 'BD',
        }

    @pico.wrap
    def parse(cls):
        one_of('+')
        caseless_string('epi')

        aggregates = {}

        if whitespace():
            while peek():
                try:
                    code = "".join(pico.one_of_strings(*(
                        tuple(cls.TOKENS) + tuple(cls.ALIAS))))
                    code = code.upper()
                except:
                    raise FormatError(
                        "Expected an epidemiological indicator "
                        "such as TB or MA.")

                # rewrite alias
                code = cls.ALIAS.get(code, code)

                if code in aggregates:
                    raise FormatError("Duplicate value for %s." % code)

                whitespace1()

                try:
                    minus = optional(partial(one_of, '-'), '')
                    value = int("".join([minus]+pico.digits()))
                except:
                    raise FormatError("Expected a value for %s." % code)

                if value < 0:
                    raise FormatError("Got %d for %s. You must "
                                      "report a positive value." % (
                        value, cls.TOKENS[code].lower()))

                aggregates[code] = value
                many(partial(one_of, ' ,;.'))

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
                previous = Aggregate.objects.filter(
                    code=code, reporter=self.user)
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
                Aggregate(code=code, value=value,
                          time=self.message.time, reporter=self.user).save()
                stats.append(stat)
            sep = [", "] * len(stats)
            if len(stats) > 1:
                sep[-2] = " and "
            sep[-1] = ""
            self.reply(u"You reported %s." % "".join(
                itertools.chain(*zip(stats, sep))))
        else:
            self.reply(u"Please include one or more reports.")

class Muac(Form):
    """Middle upper arm circumference measurement.

    Formats::

      +MUAC <name>, <sex>, <age>, <reading> [, <tag> ]*
      +MUAC <health_id>, <reading> [, <tag> ]*
      <health_id> +MUAC <reading> [, <tag> ]*

    Note that a patient id must contain one or more digits (to
    distinguish a name from a patient id).

    Reading is one of (case-insensitive):

    - ``\"red\"`` (or ``\"r\"``)
    - ``\"yellow\"`` (or ``\"y\"``)
    - ``\"green\"`` (or ``\"g\"``)

    Or, alternatively the reading may be a floating point number,
    e.g. ``\"114 mm\"`` (unit optional).
    values > 30, otherwise *cm* is assumed). While such a value will
    be translated into one of the readings above, the given number is
    still recorded.
    """

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
                reading = reading[0].upper()
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
            result['tags'] = pico.tags()

        return result

    def handle(self, health_id=None, name=None, sex=None,
               age=None, category=None, reading=None, tags=()):

        if self.user is None: # pragma: NOCOVER
            return self.reply(u"Please register before sending in reports.")

        if health_id is None:
            if isinstance(age, datetime.timedelta):
                birthdate = datetime.datetime.now() - age
            else:
                birthdate = age

            # attempt to identify the patient using the information
            patient = Patient.identify(name, sex, birthdate, self.user)

            # if we fail to identify the patient, we create a new record
            if patient is None:
                patient = Patient(
                    name=name, sex=sex, birthdate=birthdate,
                    last_reported_on_by=self.user)
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

        report = MuacMeasurement(
            reading=reading,
            category=category,
            reporter=self.user,
            patient=patient,
            time=self.message.time)

        report.save()

        sex, pronoun = ('male', 'His') if patient.sex == 'M' \
                       else ('female', 'Her')

        for tag in tags:
            value = tag.lower()
            obj = report.tags.create(value=value)
            obj.save()

        tag_string = ", ".join(tag.lower().capitalize() for tag in tags)
        if tag_string:
            tag_string = ', with ' + tag_string

        if patient.age.days > 365:
            age_string = "aged %d" % (patient.age.days % 365)
        if patient.age.days > 30:
            age_string = "(%d months old)" % (patient.age.days % 30)
        else:
            age_string = "(infant)"

        if category != 'G':
            case = Case(patient=patient, report=report)
            while case.id is None:
                try:
                    tracking_id = generate_tracking_id()
                    case.tracking_id = tracking_id
                    case.save()
                except IntegrityError: # pragma: NOCOVER
                    pass

            if category == 'Y':
                severity = "Risk of"
            else:
                severity = "Severe Acute"

            self.reply(
                "%s, %s %s has been identified with "
                "%s Malnutrition%s. Case Number %s." % (
                patient.name, sex, age_string, severity, tag_string, tracking_id))
        else:
            self.reply(
                "Thank you for reporting your measurement of "
                "%s, %s %s%s. The reading is normal (green)." % (
                    patient.name, sex, age_string, tag_string))
