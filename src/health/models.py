import collections

from django.db import models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from polymorphic import PolymorphicModel as Model
from router.models import Incoming

class Facility(Model):
    hmis = models.IntegerField(unique=True)
    name = models.CharField(max_length=50, null=True)
    location = models.CharField(max_length=50, null=True)

class Subscription(Model):
    role = models.CharField(max_length=3)
    facility = models.ForeignKey(Facility, null=True)
    user = models.ForeignKey(
        "router.User", to_field="number", related_name="subscriptions", null=True)

class Signup(Incoming):
    """Message to register as health worker."""

    role = models.CharField(max_length=3)
    facility = models.IntegerField()
    registration_required = True

    def __init__(self, role=None, facility=None, **kwargs):
        super(Signup, self).__init__(
            role=role.upper(), facility=int(facility), **kwargs)

    def __call__(self):
        if self.anonymous:
            return getattr(
                settings, "REGISTERED_USERS_ONLY_MESSAGE",
                u"You must be registered to use this service.")

        try:
            facility = Facility.objects.filter(hmis=self.facility).get()
        except ObjectDoesNotExist:
            return u"No such facility HMIS code: %d." % self.facility

        self.user.subscriptions.create(
            role=self.role,
            facility=facility)

        return (
            "You have joined the "
            "Community Vulnerability Surveillance System "
            "as a %s for %s in %s. Please resend if "
            "there is a mistake.") % (
            getattr(settings, "HEALTH_FACILITY_ROLES", {}).get(self.role, self.role),
            facility.name, facility.location)

