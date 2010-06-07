from django.contrib import admin
from . import models

admin.site.register(models.Reporter)
admin.site.register(models.Connection)
admin.site.register(models.Form)
admin.site.register(models.Incoming)
admin.site.register(models.Outgoing)
