from django.db import models
from treebeard.mp_tree import MP_Node

class LocationKind(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, primary_key=True)
    description = models.CharField(max_length=255, null=True)

    def __unicode__(self): # pragma: NOCOVER
        return self.name

class Location(MP_Node):
    latitude = models.DecimalField(decimal_places=12, max_digits=14, null=True)
    longitude = models.DecimalField(decimal_places=12, max_digits=14, null=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=50)
    kind = models.ForeignKey(LocationKind)
    node_order_by = ['name']

    class Meta:
        abstract = True

    def __unicode__(self): # pragma: NOCOVER
        return "%s %s" % (self.name, self.kind.name)

class Facility(Location):
    pass

class Area(Location):
    report_to = models.ForeignKey(Facility, null=True)
