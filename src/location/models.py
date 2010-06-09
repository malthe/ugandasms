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

    def __init__(self, *args, **kwargs):
        slug = kwargs.pop("slug", None)
        if slug is not None:
            kwargs.setdefault("kind", LocationKind.objects.get(slug=slug))
        super(Location, self).__init__(*args, **kwargs)

    def __lt__(self, other):
        return self.name < other.name

    def __gt__(self, other):
        return self.name > other.name

    def __eq__(self, other):
        return self.slug == getattr(other, "slug", other)

    def __ne__(self, other):
        return self.slug != getattr(other, "slug", other)

    def __unicode__(self): # pragma: NOCOVER
        return "%s %s" % (self.name, self.kind.name)

    def get(self):
        return type(self).objects.get(pk=self.pk)

class Facility(Location):
    pass

class Area(Location):
    report_to = models.ForeignKey(Facility, null=True, related_name="areas")
