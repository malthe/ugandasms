from django.db import models
from location.models import Area
from router.models import Form

class ReportKind(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, primary_key=True)
    description = models.CharField(max_length=255, null=True, blank=True)

class Report(models.Model):
    source = models.ForeignKey(Form, null=True)
    location = models.ForeignKey(Area, null=True)
    kind = models.ForeignKey(ReportKind)

    class Meta:
        ordering = ['-id']

    def __init__(self, *args, **kwargs):
        slug = kwargs.pop("slug", None)
        if slug is not None:
            kwargs.setdefault("kind", ReportKind.objects.get(slug=slug))
        super(Report, self).__init__(*args, **kwargs)

    @classmethod
    def from_observations(cls, slug, source=None, location=None, **observations):
        """Create a report from a set of observations.

        :param source: The form from which this report originated.
        :param location: The location at which this report happened.
        :param kind: Either a slug identifying a report kind, or a report kind object.

        In this example we'll set up an Epidemiology report for sightings of Malaria and Tuberculosis.

        >>> ObservationKind(slug="ma", name='Malaria').save()
        >>> ObservationKind(slug="tb", name='Tuberculosis').save()
        >>> ReportKind(slug="epi", name="Epidemiology").save()

        You can specify both the report kind and the observations using the slug string.

        >>> report = Report.from_observations("epi", ma=10, tb=20)
        >>> report.observations.count()
        2

        Reports created this way or automatically saved.

        >>> report.pk is not None
        True

        """

        report = Report(slug=slug, source=source, location=location)
        report.save()

        for slug, value in observations.items():
            report.observations.create(slug=slug, value=value)

        return report

class ObservationKind(models.Model):
    slug = models.SlugField(unique=True, primary_key=True)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255, null=True, blank=True)

class Observation(models.Model):
    value = models.DecimalField(max_digits=20, decimal_places=10)
    kind = models.ForeignKey(ObservationKind)
    report = models.ForeignKey(Report, related_name='observations')

    class Meta:
        ordering = ['-id']

    def __init__(self, *args, **kwargs):
        slug = kwargs.pop("slug", None)
        if slug is not None:
            kwargs.setdefault("kind", ObservationKind.objects.get(slug=slug))
        super(Observation, self).__init__(*args, **kwargs)
