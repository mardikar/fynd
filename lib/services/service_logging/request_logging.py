import StringIO
import logging

import flask


class StringLogger(object):

    def __init__(self, logger=None, logName=None, level=logging.INFO):
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(logName)
        self._oldLoggerLevel = self.logger.level
        self.logger.setLevel(level)
        self.stream = StringIO.StringIO()
        self.handler = logging.StreamHandler(stream=self.stream)
        self.logger.addHandler(self.handler)

    def getLogs(self, removeOld=False):
        value = self.stream.getValue()
        if removeOld:
            self.stream.truncate(0)
        return value

    def close(self):
        self.logger.removeHandler(self.handler)
        self.handler.close()
        self.stream.close()
        self.logger.setLevel(self._oldLoggerLevel)

    def __getattr__(self, item, default=None):
        return getattr(self.logger, item, default)


class LogEnricher(object):

    def __init__(self, logs):
        self.logs = logs

    def _enrichLogs(self):
        return dict(LOG_STRING=self.logs)

    @classmethod
    def enrich(cls, logs):
        return cls(logs)._enrichLogs()


class StorageHandler(object):

    def __init__(self, enrichedLogs):
        self.logs = enrichedLogs

    def _storeLogs(self):
        logging.info("Would have stored %s" % self.logs)

    @classmethod
    def store(cls, enrichedLogs):
        return cls(enrichedLogs)._storeLogs()


class RequestLoggingContext(object):
    """
    Use this in request context
    """

    def __init__(self, logger=None, logLevel=logging.INFO, autoStore=False, storageHandler=None, logEnricher=None):
        self.logLevel = logLevel
        self.logger = logger
        self.autoStore = autoStore
        self.storageHandler = storageHandler or StorageHandler
        self.logEnricher = logEnricher or LogEnricher

    def __enter__(self):
        self.logger = StringLogger(self.logLevel) if not self.logger else self.logger

    def storeLogs(self):
        if self.autoStore:
            logs = self.logger.getLogs()
            enrichedLog = self.logEnricher.enrich(logs)
            self.storageHandler.store(enrichedLog)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.storeLogs()
        self.logger.close()


class FlaskLogEnricher(LogEnricher):

    def _enrichLogs(self):
        enrichedLogs = LogEnricher._enrichLogs()
        enrichedLogs['USER'] = flask.request.remote_user
        enrichedLogs['URL'] = flask.request.url
        enrichedLogs['HTTP_METHOD'] = flask.request.method
        enrichedLogs['USER_AGENT'] = flask.request.user_agent
        enrichedLogs.update(flask.g.metadata)
        return enrichedLogs


class FlaskRequestLoggingContext(RequestLoggingContext):

    def __init__(self, logger=None, logLevel=None, autoStore=None, storageHandler=None, logEnricher=FlaskLogEnricher):
        RequestLoggingContext.__init__(self, logger=logger, logLevel=logLevel, autoStore=autoStore,
                                       storageHandler=storageHandler, logEnricher=logEnricher)
