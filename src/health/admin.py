from django.contrib import admin
from . import models

admin.site.register(models.Patient)
admin.site.register(models.Case)
admin.site.register(models.MuacMeasurement)
admin.site.register(models.Aggregate)
