import flask

from lib.io.validators.json_schema_validtor import validate


class ImdbJsonSchemaValidtor(object):
    JSON_SCHEMA_DEFINITIONS = {
        'name': {
            'type': 'string'
        },
        'genres': {
            'type': 'array',
            'items': {
                'type': 'string'
            },
        },
        'director': {
            'type': 'string',
        },
        'imdb_score': {
            'type': 'number',
            'minimum': 0,
            'maximum': 10,
        },
        'popularity': {
            'type': 'number',
            'minimum': 0,
            'maximum': 100
        }
    }

    POST_JSON_SCHEMA = {
        'type': 'array',
        'items': {'$ref': '#/definitions/movies'},
        'definitions': {
            'movies': {
                'type': 'object',
                'additionalProperties': False,
                'properties': JSON_SCHEMA_DEFINITIONS,
                'required': ["name", "director", "imdb_score", "genres"]
            }
        },
    }

    PUT_JSON_SCHEMA = {
        'type': 'array',
        'items': {'$ref': '#/definitions/movies'},
        'definitions': {
            'movies': {
                'type': 'object',
                'additionalProperties': False,
                'properties': JSON_SCHEMA_DEFINITIONS,
                'required': ["name", "director", "imdb_score"]
            }
        },
    }

    DELETE_JSON_SCHEMA = {
        'type': 'array',
        'items': {'$ref': '#/definitions/movies'},
        'definitions': {
            'movies': {
                'type': 'object',
                'additionalProperties': False,
                'properties': JSON_SCHEMA_DEFINITIONS,
                'required': ["name", "director"]
            }
        },
    }

    @classmethod
    def validate(cls, jsonData):
        validate(getattr(cls, "%s_JSON_SCHEMA" % flask.request.method.upper()), jsonData)
