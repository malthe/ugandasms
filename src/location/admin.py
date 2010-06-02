from . import models
from treebeard.admin import TreeAdmin
from django.contrib import admin

class AreaAdmin(TreeAdmin):
    pass

class FacilityAdmin(TreeAdmin):
    pass

admin.site.register(models.Area, AreaAdmin)
admin.site.register(models.Facility, FacilityAdmin)
