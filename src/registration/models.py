from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from polymorphic import PolymorphicModel as Model
from router.models import Incoming

class User(Model):
    number = models.CharField(max_length=12, unique=True)
    name = models.CharField(max_length=50, null=True)
    location = models.CharField(max_length=50, null=True)

    class Meta:
        app_label = "router"

    def __unicode__(self):
        return self.name

# models.loading.register_models('router', User)

class Registration(Incoming):
    """Register with the system."""

    name = models.CharField(max_length=50, null=True)
    location = models.CharField(max_length=50, null=True)

    def __call__(self):
        try:
            user = self.user
        except ObjectDoesNotExist:
            user = User(
                number=self.sender,
                name = self.name,
                location = self.location,
                )

            user.save()
            return (
                "Welcome, %(name)s (#%(id)04d). "
                "You have been registered.") % {
                'name': self.name,
                'id': user.id,
                }

        user.name = self.name
        user.location = self.location
        user.save()

        return (
            "Hello, %(name)s (#%(id)04d). "
            "You have updated your information.") % {
            'name': self.name,
            'id': user.id,
            }




