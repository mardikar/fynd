import simplejson


class JsonSerializer(object):

    DEFAULT_SERIALIZERS = dict()
    DEFAULT_DESERIALIZERS = dict()

    def __int__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    @classmethod
    def fromJson(cls, jsonString):
        return simplejson.loads(jsonString)

    @classmethod
    def toJson(cls, obj, **kwargs):
        return simplejson.dumps(obj)
