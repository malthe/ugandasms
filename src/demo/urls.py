from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

from router.views import kannel

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
)
