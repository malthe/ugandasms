from django.db import models
from polymorphic import PolymorphicModel as Model

from ..models import Incoming

class User(Model):
    number = models.CharField(max_length=12, unique=True)

    class Meta:
        app_label = 'router'

class Echo(Incoming):
    def __call__(self):
        return self.text
