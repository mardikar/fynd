import flask
import logging

from imdb.cache import ImdbCache
from lib.io.serializer.json_serializer import JsonSerializer
from lib.services.rest.flask_service.base import ServiceBase, createJsonResponse, app
from imdb.imdb_json_schemas import ImdbJsonSchemaValidtor

application = app


class HttpMethods(object):
    GET = "GET"
    DELETE = "DELETE"
    POST = "POST"
    PUT = "PUT"


class ImdbService(ServiceBase):

    def __init__(self):
        ServiceBase.__init__(self)
        self.cache = ImdbCache()

    def registerOperations(self):
        baseUrl = "/imdb/api/v1/"
        self.registerOperation(baseUrl, self.handleMovie,\
                               [HttpMethods.GET, HttpMethods.DELETE, HttpMethods.POST, HttpMethods.PUT])

    @property
    def postData(self):
        data = JsonSerializer.fromJson(flask.request.data)['data']
        ImdbJsonSchemaValidtor.validate(data)
        return data

    def addMovie(self):
        try:
            self.cache.add(self.postData)
            data = dict(data="OK")
        except Exception as e:
            data = dict(errors=dict(message=str(e)))
        return createJsonResponse(JsonSerializer.toJson(data))

    def deleteMovie(self):
        try:
            self.cache.delete(self.postData)
            data = dict(data="OK")
        except Exception as e:
            data = dict(errors=dict(message=str(e)))
        return createJsonResponse(JsonSerializer.toJson(data))

    def editMovie(self):
        try:
            self.cache.update(self.postData)
            data = dict(data="OK")
        except Exception as e:
            data = dict(errors=dict(message=str(e)))
        return createJsonResponse(JsonSerializer.toJson(data))

    def getMovie(self):
        qp = flask.request.args.to_dict()
        return self._getMovie(qp)

    def _getMovie(self, qp):
        data = JsonSerializer.toJson(self.cache.get(**qp))
        return createJsonResponse(data)

    def handleMovie(self):
        httpMethod = flask.request.method.upper()
        if httpMethod == HttpMethods.POST:
            return self.addMovie()
        elif httpMethod == HttpMethods.PUT:
            return self.editMovie()
        elif httpMethod == HttpMethods.DELETE:
            return self.deleteMovie()
        elif httpMethod == HttpMethods.GET:
            return self.getMovie()
        raise Exception("%s method is not supported" % httpMethod)

    def run(self):
        pass

    def start(self):
        self.cache.start()
        ServiceBase.start(self)

    def stop(self):
        self.cache.stop()
        ServiceBase.stop(self)


if __name__ == '__main__':
    ImdbService().start()
    application.run(host=application['HOST'], port=application['PORT'])
