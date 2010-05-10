from django.conf.urls.defaults import *
from django.contrib import admin
from router.views import kannel

admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'^admin/', include(admin.site.urls)),
    (r'^kannel/', kannel),
    )
