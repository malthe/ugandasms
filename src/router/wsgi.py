import imp

from django import conf
from django import utils
from django.core.handlers.wsgi import WSGIHandler
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured

# store transports at module-level to prevent gc
_transports = {}

def make_app(config, settings=None):
    imp.load_source("settings", settings)
    settings = conf.Settings("settings")
    conf.settings.configure(settings)
    utils.translation.activate(conf.settings.LANGUAGE_CODE)

    # start transports
    for name, options in getattr(settings, "TRANSPORTS", {}).items():
        try:
            path = options.pop("TRANSPORT")
        except KeyError: # PRAGMA: nocover
            raise ImproperlyConfigured(
                "Unable to configure the '%s' transport. "
                "Must set value for ``TRANSPORT``." % name)

        module_name, class_name = path.rsplit('.', 1)
        module = import_module(module_name)
        factory = getattr(module, class_name)
        _transports[name] = factory(name, options)

    app = WSGIHandler()
    return app
