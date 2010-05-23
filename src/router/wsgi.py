import imp
import signal

from django import conf
from django import utils
from django.core.handlers.wsgi import WSGIHandler
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured

# store transports at module-level to prevent gc
_transports = {}

# store old interrupt handlers
_default_handlers = {}

def shutdown(signum, frame):
    from router.transports import hangup
    hangup.send(sender=signum)
    _default_handlers[signum](signum, frame)

def make_app(config, settings=None):
    imp.load_source("settings", settings)
    settings = conf.Settings("settings")
    conf.settings.configure(settings)
    utils.translation.activate(conf.settings.LANGUAGE_CODE)
    return make_app_from_settings(settings)

def make_app_from_settings(settings):
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
    _default_handlers[signal.SIGHUP] = signal.signal(signal.SIGHUP, shutdown)
    _default_handlers[signal.SIGINT] = signal.signal(signal.SIGINT, shutdown)
    return app
