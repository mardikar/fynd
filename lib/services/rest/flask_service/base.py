import logging
import time
import traceback

import flask
import wrapt

from lib.services.service_logging.request_logging import FlaskRequestLoggingContext

logger = logging

@wrapt.decorator
def operation(wrapped, instance, args, kwargs):
    try:
        return wrapped(*args, **kwargs)
    except Exception as e:
        if not hasattr(flask.g, 'metadata'):
            flask.g.metadata = dict()
        flask.g.metadata['error'] = dict(
            message=str(e),
            traceback=traceback.format_exc()
        )
        logger.info("Caught Exception %s" % e)
        raise e


def createJsonResponse(jsonData, statusCode=200, headers=None):
    """
    create a flaks response from json data and status
    :param jsonData: json string response
    :param statusCode: HTTP status code
    :param headers: HTTP header overrides - default used otherwise
    :return: flask.Response object
    """
    defaultHeaders = {
        'Content-Type': "application/json",
        'Access-Control-Allow-Headers': "Content-Type, Authorization, Content-Length, X-Requested-With",
        'Access-Control-Allow-Methods': "GET, POST, PUT, DELETE",
        'Access-Control-Allow-Origin': "*"
    }
    defaultHeaders.update(headers or dict())
    return flask.Response(jsonData, status=statusCode, headers=defaultHeaders)


class ServiceBase(object):
    SERVICE_NAME = "base"
    SERVICE_ALIAS = "base"
    BASE_ENDPOINT = "/base/api/v1/"

    def __init__(self, app):
        self.app = app
        self.serverModule = flask.Blueprint(self.SERVICE_NAME, __name__)
        self._operations = dict()

    @staticmethod
    def _startLoggingContext():
        """
        start the logging context for each request
        :return:
        """
        flask.g.loggingContext = FlaskRequestLoggingContext(autoStore=True)
        flask.g.metadata = dict(
            STARTTIME=time.time(),
        )
        flask.g.loggingContext.__enter__()

    @staticmethod
    def _stopLoggingContext(response):
        """
        stop the logging context
        :param response:
        :return:
        """
        endTime = time.time()
        flask.g.metadata.update(dict(ENDTIME=endTime, DURATIONMS=endTime - flask.g.metadata['STARTTIME']))
        flask.g.loggingContext.__exit__(None, None, None)

    def before_request(self):
        self._startLoggingContext()

    def after_request(self, response):
        self._stopLoggingContext(response)
        return response

    def registerOperations(self):
        """
        override this in sub-class
        :return:
        """
        pass

    def registerOperation(self, url, handler, httpMethods=["GET"]):
        """
        register a url and handler
        :param url:
        :param handler:
        :param httpMethods:
        :return:
        """
        self.serverModule.add_url_rule(url, view_func=operation(handler), methods=httpMethods)
        self._operations.setdefault(url, []).extend(httpMethods)
        logging.info("Registered!")

    def run(self):
        self.app.run(debug=True)

    def start(self):
        """
        register after request, before request handlers
        register operations
        and spin up the flaks application
        :return:
        """
        self.app.after_request(self.after_request)
        self.app.before_request(self.before_request)
        self.registerOperations()
        self.app.register_blueprint(self.serverModule)
        logger.warn(self.app.url_map)
        logger.warn("Started Service")
        self.run()

    def stop(self):
        pass
