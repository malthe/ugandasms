import imp

from django import conf
from django import utils
from django.core.handlers.wsgi import WSGIHandler

def make_app(config, settings=None):
    imp.load_source("settings", settings)
    settings = conf.Settings("settings")
    conf.settings.configure(settings)
    utils.translation.activate(conf.settings.LANGUAGE_CODE)

    app = WSGIHandler()
    return app
