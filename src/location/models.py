import mptt

from django.db import models

class LocationKind(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255, null=True)

class Location(models.Model):
    latitude = models.DecimalField()
    longitude = models.DecimalField()
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=50, blank=True, null=True)
    kind = models.ForeignKey(LocationKind)
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children')

mptt.register(Location, order_insertion_by=['name'])
