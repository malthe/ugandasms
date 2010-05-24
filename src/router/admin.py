from django.contrib import admin
from . import models

admin.site.register(models.User)
admin.site.register(models.Peer)
admin.site.register(models.Form)
admin.site.register(models.Incoming)
admin.site.register(models.Outgoing)
