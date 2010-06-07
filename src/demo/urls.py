from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

from django.contrib import admin
from django.contrib.auth.views import login
from django.contrib.auth.views import logout

admin.autodiscover()

import logui.urls
import webui.urls

urlpatterns = patterns(
    '',
    url(r'^login$', login),
    url(r'^logout$', logout),
    url(r'^admin/', include(admin.site.urls)),
    ) + \
    logui.urls.urlpatterns + \
    webui.urls.urlpatterns


