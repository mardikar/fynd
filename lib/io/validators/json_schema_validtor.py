import jsonschema


def validate(schema, jsonData, cls=None, *args, **kwargs):
    jsonschema.validate(jsonData, schema, cls=cls, *args, **kwargs)
