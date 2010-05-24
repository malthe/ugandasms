import itertools
import datetime

from polymorphic import PolymorphicModel as Model

from django.db import models
from django.conf import settings

from picoparse import any_token
from picoparse import choice
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

from router.pico import comma
from router.pico import date
from router.pico import digits
from router.pico import identifier
from router.pico import name
from router.pico import one_of_strings
from router.pico import separator
from router.pico import tags
from router.pico import timedelta
from router.pico import wrap as pico
from router.models import Form
from router.models import User
from router.router import FormatError

date = partial(date, formats=settings.DATE_INPUT_FORMATS)

class Patient(Model):
    health_id = models.CharField(max_length=30, null=True)
    name = models.CharField(max_length=50, null=True)
    sex = models.CharField(max_length=1, null=True)
    birthdate = models.DateTimeField(null=True)

    @property
    def age(self):
        if self.birthdate is not None:
            return datetime.now() - self.birthdate

class Report(Model):
    """Health report."""

    reporter = models.ForeignKey(User)
    tags = ()

class Tag(Model):
    report = models.ForeignKey(Report, related_name="tags")
    value = models.CharField(max_length=20)

class Incident(Report):
    """An incident is a health report tied to an individual."""

    patient = models.ForeignKey(Patient, null=True)

class Aggregate(Report):
    code = models.CharField(max_length=2, db_index=True)
    time = models.DateTimeField(db_index=True)
    value = models.IntegerField()

    class Meta:
        ordering = ['-id']

class Malnutrition(Incident):
    reading = models.CharField(max_length=1)
    value = models.FloatField(null=True)

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

    @pico
    def parse(cls):
        one_of('+')
        caseless_string('epi')

        aggregates = {}

        if whitespace():
            while peek():
                try:
                    code = "".join(one_of_strings(*(
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
                    value = int("".join([minus]+digits()))
                except:
                    raise FormatError("Expected a value for %s." % code)

                if value < 0:
                    raise FormatError("Got %d for %s. You must "
                                      "report a positive value." % (
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
    """MUAC report.

    Formats::

      +MUAC <name>, <sex>, <age>, <reading> [, <tag> ]*
      +MUAC <patient_id>, <reading> [, <tag> ]*
      <patient_id> +MUAC <reading> [, <tag> ]*

    Note that a patient id must contain one or more digits (to
    distinguish a name from a patient id).

    Reading is one of (case-insensitive):

    - ``\"red\"`` (or ``\"r\"``)
    - ``\"yellow\"`` (or ``\"y\"``)
    - ``\"green\"`` (or ``\"g\"``)

    Or, alternatively the reading may be a floating point number,
    e.g. ``\"114 mm\"`` (unit optional; *mm* is default unit for
    values > 30, otherwise *cm* is assumed). While such a value will
    be translated into one of the readings above, the given number is
    still recorded.
    """

    @staticmethod
    def get_reading_in_mm(reading):
        if reading > 30:
            return reading
        return reading*10

    @pico
    def parse(self):
        result = {}

        prefix = optional(tri(identifier), None)
        if prefix is not None:
            result['patient_id'] = "".join(prefix)
            whitespace()

        one_of('+')
        caseless_string('muac')

        if prefix is None:
            try:
                whitespace1()
                part = optional(tri(identifier), None)
                if part is not None:
                    result['patient_id'] = "".join(part)
                else:
                    result['name'] = name()
            except:
                raise FormatError("Expected a patient id or name.")

        if 'name' in result:
            try:
                separator()
                result['sex'] = one_of('MmFf').upper()
            except:
                raise FormatError("Expected either M or F to indicate the patient's gender.")

            try:
                separator()
            except:
                raise FormatError("Expected age or birthdate of patient.")

            try:
                result['age'] = choice(*map(tri, (date, timedelta)))
            except:
                received, stop = many_until(any_token, comma)
                raise FormatError("Expected age or birthdate of patient, but "
                                 "received %s." % "".join(received))
        try:
            if prefix is None:
                separator()
            else:
                whitespace1()

            reading = choice(
                partial(one_of_strings, 'red', 'green', 'yellow', 'r', 'g', 'y'),
                digits)

            try:
                reading = int("".join(reading))
            except:
                reading = reading[0].upper()
            else:
                whitespace()
                unit = optional(partial(one_of_strings, 'mm', 'cm'), None)
                if unit is None:
                    reading = self.get_reading_in_mm(reading)
                elif "".join(unit) == 'cm':
                    reading = reading * 10
            result['reading'] = reading
        except:
            raise FormatError(
                "Expected MUAC reading (either green, yellow or red), but "
                "received %s." % "".join(remaining()))

        if optional(separator, None):
            result['tags'] = tags()

        return result

    @staticmethod
    def handle(patient_id=None, name=None, sex=None, age=None, reading=None, tags=()):
        if isinstance(age, datetime.timedelta):
            age = datetime.now() - age
