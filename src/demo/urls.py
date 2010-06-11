from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

from django.contrib import admin
from django.contrib.auth.views import login
from django.contrib.auth.views import logout

admin.autodiscover()

import messageui.urls
import webui.urls
import stats.urls
import reporterui.urls

urlpatterns = patterns(
    '',
    url(r'^login$', login),
    url(r'^logout$', logout),
    url(r'^admin/', include(admin.site.urls)),
    ) + \
    messageui.urls.urlpatterns + \
    stats.urls.urlpatterns + \
    webui.urls.urlpatterns + \
    reporterui.urls.urlpatterns


