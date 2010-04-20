import os
import otto
import datetime
import webob.exc
import chameleon.zpt.loader
import chameleon.core.config

from . import dashboard

loader = chameleon.zpt.loader.TemplateLoader(
    os.path.join(os.path.dirname(__file__), "templates"),
    auto_reload=chameleon.core.config.DEBUG_MODE)

time = datetime.datetime.now()

def template(filename):
    inst = loader.load(filename)
    def decorator(func):
        def wrapper(*args):
            kwargs = func(*args)
            delta = datetime.datetime.now() - time
            if delta.days > 0:
                denominator, value = "days", delta.days
            elif delta.seconds > 3600:
                denominator, value = "hours", delta.seconds // 3600
            elif delta.seconds > 60:
                denominator, value = "minutes", delta.seconds // 60
            else:
                denominator, value = "seconds", delta.seconds

            uptime = "%s (%d %s ago)" % (
                time.strftime("%A, %d. %B %Y %I:%M %p"),
                value, denominator[:len(denominator) - int(value == 1)])

            result = inst(
                uptime=uptime,
                load=loader.load,
                **kwargs)
            return webob.Response(result)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

class WSGIApp(otto.Application):
    def __init__(self):
        super(WSGIApp, self).__init__()
        self.connect("/", self.index)
        self.connect("/users", self.users)
        self.connect("/accounts/login", self.login)

    @template("index.pt")
    def index(self, request):
        return {
            'latest_reports': dashboard.get_reports(limit=3),
            }

    @template("login.pt")
    def login(self, request):
        return {}

    @template("users.pt")
    def users(self, request):
        return {}

def make_dashboard(*args):
    return WSGIApp()

