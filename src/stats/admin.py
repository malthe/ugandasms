from django.contrib import admin
from . import models

admin.site.register(models.Observation)
admin.site.register(models.ObservationKind)
admin.site.register(models.Report)
admin.site.register(models.ReportKind)
