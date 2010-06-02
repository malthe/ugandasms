from django.db import models
from location.models import Area
from router.models import Form

class ReportKind(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)

class Report(models.Model):
    source = models.ForeignKey(Form, null=True)
    location = models.ForeignKey(Area, null=True)
    kind = models.ForeignKey(ReportKind)
    
    @classmethod
    def from_observations(cls, kind, source=None, location=None, **observations):
        """Create a report from a set of observations.
        
        :param source: The form from which this report originated.
        :param location: The location at which this report happened.
        :param kind: Either a slug identifying a report kind, or a report kind object.
        
        In this example we'll set up an Epidemiology report for sightings of Malaria and Tuberculosis.
        
        >>> ObservationKind(slug="ma", name='Malaria').save()
        >>> ObservationKind(slug="tb", name='Tuberculosis').save()
        >>> ReportKind(slug="epi", name="Epidemiology").save()
        
        You can specify both the report kind and the observations using the slug string.
        
        >>> report1 = Report.from_observations("epi", ma=10, tb=20)
        >>> report1.observations.count()
        2
        
        Alternatively, you may provide the report kind as the object.

        >>> report2 = Report.from_observations(report1.kind, ma=10, tb=20)
        >>> report2.observations.count()
        2
       
        """
        
        if isinstance(kind, basestring):
            kind = ReportKind.objects.get(slug=kind)
        
        report = Report(source=source, location=location, kind=kind)
        report.save()
        
        for slug, value in observations.items():
            kind = ObservationKind.objects.get(slug=slug)
            observation = Observation(kind=kind, value=value, report=report)
            observation.save()
            
        return report

class ObservationKind(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    
class Observation(models.Model):
    value = models.DecimalField(max_digits=20, decimal_places=10)
    kind = models.ForeignKey(ObservationKind)
    report = models.ForeignKey(Report, related_name='observations')
