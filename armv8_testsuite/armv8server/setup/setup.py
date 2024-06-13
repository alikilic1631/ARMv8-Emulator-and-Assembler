# 3rd party imports
from flask import Flask
import jinja2
from jinja2.ext import Extension
from jinja2.exceptions import TemplateRuntimeError

import armv8server.setup.routes as routes
import armv8suite as suite


class RaiseExtension(Extension):
    tags = {"raise"}
    
    def parse(self, parser):
        lineno = next(parser.stream).lineno
        args = [parser.parse_expression()]
        return jinja2.environment.nodes.CallBlock(self.call_method("_raise", args), [], [], []).set_lineno(lineno)

    def _raise(self, msg, caller):
        raise TemplateRuntimeError(msg)


def add_routes(app: Flask):
    """ Add routes to the app context to be used in jinja templates via `routes` and `params` """
    @app.context_processor
    def inject_routes():
        return dict(
            routes=routes.WebRoutes,
            params=routes.Params,
            suite=suite
        )

def setup_app(app: Flask):
    app.jinja_env.add_extension(RaiseExtension)
    add_routes(app)



