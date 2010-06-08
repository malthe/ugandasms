#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *

from .views import dashboard

urlpatterns = patterns(
    '',
    url(r'^$', dashboard),
)

