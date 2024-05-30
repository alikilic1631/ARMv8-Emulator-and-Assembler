from __future__ import annotations

# 3rd party imports
import flask
from flask import render_template

# local imports

from armv8server import app
from armv8server.setup.setup import setup_app
from armv8server.setup.routes import WebRoutes
import armv8server.server.server as server
from armv8suite.data.result import TestType


###################################################################################################
# Template Pages
setup_app(app)


# homepage
@app.route(WebRoutes.homepage.route)
def index():
    return render_template("index.jinja")


# page to find specific test to assemble
# @app.route(WebRoutes.find_test.route)
@app.route(WebRoutes.find_test.route)
def find_test(fname: str):
    try:
        test_type = TestType.from_str(fname)
    except ValueError as e:
        app.logger.error(f"Invalid test type: {fname}")
        return flask.redirect(WebRoutes.homepage.route)
        
    return server.find_test(test_type)

###################################################################################################
# Run All Tests


@app.route(WebRoutes.assemble_all.route, methods=["GET", "POST"])
def assemble_all_tests() -> str:
    """ page to assemble all tests """
    app.logger.info("Assembling all tests")
    return server.assemble_all_tests()


@app.route(WebRoutes.emulate_all.route, methods=["GET", "POST"])
def emulate_all_tests() -> str:
    """ page to emulate all tests """
    app.logger.info("Emulating all tests")
    return server.emulate_all_tests()


###################################################################################################
# Single Tests

@app.route(WebRoutes.assemble_single.route)
def assemble_individual():
    """ page to assemble a single test """
    test_file = flask.request.args.get(WebRoutes.assemble_single.test_file.key)
    if test_file is None:
        return flask.redirect(WebRoutes.find_test.route)
    
    return server.assemble_individual(test_file)


@app.route(WebRoutes.emulate_single.route)
def emulate_individual():
    """ page to emulate a single test """
    test_file = flask.request.args.get(WebRoutes.emulate_single.test_file.key)
    if test_file is None:
        return flask.redirect(WebRoutes.find_test.route)
    
    return server.emulate_individual(test_file)


###################################################################################################
# Main


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()
