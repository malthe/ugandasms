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
from router.models import User
from router.router import FormatError

date = partial(pico.date, formats=settings.DATE_INPUT_FORMATS)

TRACKING_ID_LETTERS = tuple('ABCDEFGHJKLMPQRTUVXZ')

def generate_tracking_id():
    return '%2.d%s%s%2.d' % (
        random.randint(0, 99),
        random.choice(TRACKING_ID_LETTERS),
        random.choice(TRACKING_ID_LETTERS),
        random.randint(0, 99))

class Patient(Model):
    health_id = models.CharField(max_length=30, null=True)
    name = models.CharField(max_length=50)
    sex = models.CharField(max_length=1)
    birthdate = models.DateTimeField()
    deathdate = models.DateTimeField(null=True)
    last_reported_on_by = models.ForeignKey(User)

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
    closed = models.DateTimeField(null=True)

class Aggregate(Report):
    """An aggregate occurrence report codified by a two-letter
    keyword."""

    code = models.CharField(max_length=2, db_index=True)
    value = models.IntegerField()
    total = models.IntegerField(null=True)

class Birth(Report):
    patient = models.ForeignKey(Patient)
    location = models.CharField(max_length=25)

class MuacMeasurement(Report):
    """Measurement record of the MUAC heuristic."""

    category = models.CharField(max_length=1)
    reading = models.FloatField(null=True)
    patient = models.ForeignKey(Patient, null=True)

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
                result['location'] = matches[0].upper()
                break
        else:
            raise FormatError(
                "Did not understand the location: %s." % words)

        return result

    def handle(self, name=None, sex=None, location=None):
        if self.user is None: # pragma: NOCOVER
            return self.reply(u"Please register before sending in reports.")

        birthdate = datetime.datetime.now()

        patient = Patient(
            name=name, sex=sex, birthdate=birthdate,
            last_reported_on_by=self.user)
        patient.save()

        birth = Birth(patient=patient, location=location,
                      reporter=self.user, time=self.message.time)
        birth.save()

        self.reply("Thank you for registering the birth of %s." % \
                   patient.label)

class DeathForm(Form):
    """Report a death.

    Format::

      +DEATH <name>, <sex>, <age>
      +DEATH [<health_id>]+
      +DEATH [<tracking_id>]+

    """

    prompt = "Death: "

    @pico.wrap
    def parse(cls):
        one_of('+')
        caseless_string('death')

        result = {}

        identifiers = optional(pico.ids, None)
        if identifiers:
            result['ids'] = [id.upper() for id in identifiers]
        else:
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
                pico.separator()
            except:
                raise FormatError("Expected age or birthdate of patient.")

            try:
                result['age'] = choice(*map(tri, (pico.date, pico.timedelta)))
            except:
                received, stop = many_until(any_token, pico.comma)
                raise FormatError("Expected age or birthdate of patient, but "
                                 "received %s." % "".join(received))

        return result

    def handle(self, ids=None, name=None, sex=None, age=None):
        if self.user is None: # pragma: NOCOVER
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

            cases = [case for case in cases if case.closed is None]
            for case in cases:
                case.closed = self.message.time
                case.save()
        else:
            if isinstance(age, datetime.timedelta):
                birthdate = datetime.datetime.now() - age
            else:
                birthdate = age

            patient = Patient.identify(name, sex, birthdate, self.user)
            if patient is None:
                return self.reply(
                    u"We have recorded the death of %s." % name)

            cases = patient.cases.all()
            patients = [patient]

        for patient in patients:
            patient.deathdate = self.message.time
            patient.save()

        for case in cases:
            if case.report.reporter != self.user:
                self.reply("We have received notice of the death "
                           "of your patient %s." % case.patient.label)

        self.reply(
            "Thank you for reporting the death of %s. "
            "We have closed %d open case(s)." % (
                ", ".join(patient.label for patient in patients),
                len(cases)))

class Cure(Form):
    """Mark a case as closed due to curing.

    Format::

      +CURE [<tracking_id>]+

    Separate multiple entries with space and/or comma. Tracking IDs
    are case-insensitive.
    """

    prompt = "Cured: "

    @pico.wrap
    def parse(cls):
        one_of('+')
        caseless_string('cure')

        try:
            whitespace1()
            tracking_ids = pico.ids()
        except:
            raise FormatError("Expected tracking id (got: %s)." % \
                              "".join(remaining()))

        if not tracking_ids:
            raise FormatError(
                "Please specify one or more tracking IDs.")

        return {'tracking_ids': [tid.upper() for tid in tracking_ids]}

    def handle(self, tracking_ids=None):
        cases = Case.objects.filter(tracking_id__in=tracking_ids).all()

        found = set([case.tracking_id for case in cases])
        not_found = set(tracking_ids) - found

        if not_found:
            return self.reply(
                "The case number(s) %s do not exist. "
                "Please correct and resend all tracking ids."  % \
                ", ".join(not_found))

        for case in cases:
            case.closed = self.message.time
            case.save()
            label = case.patient.label
            reporter = case.report.reporter

            if reporter != self.user:
                self.reply("Your patient, %s, has been set as \"cured\"." % (
                    label), reporter)

        self.reply("You have closed %d case(s)." % len(cases))

class Aggregates(Form):
    """Report on aggregate data.

    This form supports the following aggregate indicators:

    * Epidemiology
    * Domestic

    For flexible use, multiple command strings are accepted::

      +AGG
      +EPI
      +HOME

    Regular reports should come in with the format::

      [<total>, ]? [<token> <integer_value>]*

    The ``token`` must be one of the keys defined in
    ``TOKENS``. Negative values are not allowed.

    Example input for 12 cases of malaria and 4 tuberculous cases::

      +EPI MA 12, TB 4

    The reports are confirmed in the reply, along with percentage or
    absolute change (whichever is applicable depending on whether this
    or the previous value is zero) on consecutive reporting.

    Example output::

      You reported malaria 12 (+5) and tuberculosis 4 (+23%).

    All aggregates are entered into the database as separate
    objects. To group aggregates based on reports, filter by user and
    group by time.
    """

    TOKENS = {
        # epidemiological indicators
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
        # domestic indicators
        'WA': 'Safe Drinking Water',
        'HA': 'Handwashing Facilities',
        'LA': 'Latrines',
        'IT': 'ITTNs/LLINs',
        }

    ALIAS = {
        'DY': 'BD',
        }

    prompt = "Report: "

    @pico.wrap
    def parse(cls):
        one_of('+')
        pico.one_of_strings('agg', 'epi', 'home')

        aggregates = {}
        result = {'aggregates': aggregates}

        if whitespace():
            total = "".join(optional(pico.digits, ()))
            if total:
                result['total'] = int(total)
                many1(partial(one_of, ' ,;'))

            while peek():
                try:
                    code = "".join(pico.one_of_strings(*(
                        tuple(cls.TOKENS) + tuple(cls.ALIAS))))
                    code = code.upper()
                except:
                    raise FormatError(
                        "Expected an indicator code "
                        "such as TB or MA (got: %s)." % \
                        "".join(remaining()))

                # rewrite alias
                code = cls.ALIAS.get(code, code)

                if code in aggregates:
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
                        value, cls.TOKENS[code]))

                aggregates[code] = value
                many(partial(one_of, ' ,;.'))

        return result

    def handle(self, total=None, aggregates={}):
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
                Aggregate(code=code, value=value, total=total,
                          time=self.message.time, reporter=self.user).save()
                stats.append(stat)
            separator = [", "] * len(stats)
            if len(stats) > 1:
                separator[-2] = " and "
            separator[-1] = ""
            self.reply(u"You reported %s." % "".join(
                itertools.chain(*zip(stats, separator))))
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

        pronoun = 'his' if patient.sex == 'M' else 'her'

        for tag in tags:
            value = tag.lower()
            obj = report.tags.create(value=value)
            obj.save()

        tag_string = ", ".join(tag.lower().capitalize() for tag in tags)
        if tag_string:
            tag_string = ', with ' + tag_string

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
                "%s has been identified with "
                "%s Malnutrition%s. %s Case Number %s." % (
                patient.label, severity, tag_string, pronoun.capitalize(),
                    tracking_id))
        else:
            self.reply(
                "Thank you for reporting your measurement of "
                "%s%s. %s reading is normal (green)." % (
                    patient.label, tag_string, pronoun.capitalize()))
