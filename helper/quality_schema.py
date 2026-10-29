# -*- coding: utf-8 -*-
"""Strict contracts for scoped audits and literal fragment patches."""
def object_schema(properties):
    return {'type': 'object', 'properties': properties, 'required': list(properties), 'additionalProperties': False}


def schema(operation):
    string = {'type': 'string'}
    ids = {'type': 'array', 'minItems': 1, 'maxItems': 23, 'items': {'type': 'integer', 'minimum': 1, 'maximum': 23}}
    sources = {'type': 'array', 'maxItems': 12, 'items': object_schema({
        'url': string, 'title': string, 'publisher': string, 'edition': string, 'section': string, 'quote': string})}
    if operation == 'patch':
        return object_schema({'version': {'type': 'integer', 'enum': [2]}, 'fingerprint': string, 'criteriaIds': ids,
            'replacements': {'type': 'array', 'maxItems': 30, 'items': object_schema({
                'before': string, 'after': string, 'criteriaIds': ids, 'reason': string})},
            'seo': object_schema({'title': string, 'description': string, 'h1': string}), 'sources': sources,
            'notes': {'type': 'array', 'maxItems': 20, 'items': string}})
    if operation == 'focused_audit':
        return object_schema({'version': {'type': 'integer', 'enum': [2]}, 'fingerprint': string,
            'criteria': {'type': 'array', 'minItems': 1, 'maxItems': 23, 'items': object_schema({
                'id': {'type': 'integer', 'minimum': 1, 'maximum': 23},
                'status': {'type': 'string', 'enum': ['pass', 'problem', 'unverified', 'na']}, 'reason': string})},
            'issues': {'type': 'array', 'maxItems': 200, 'items': object_schema({
                'criterion': {'type': 'integer', 'minimum': 1, 'maximum': 23},
                'severity': {'type': 'string', 'enum': ['blocker', 'warning']}, 'title': string,
                'quote': string, 'why': string, 'action': string})},
            'facts': {'type': 'array', 'maxItems': 300, 'items': object_schema({
                'claim': string, 'sourceUrl': string, 'sourceQuote': string})}, 'sources': sources,
            'visuals': {'type': 'array', 'maxItems': 11, 'items': object_schema({
                'assetId': string, 'status': {'type': 'string', 'enum': ['pass', 'problem', 'unverified']}, 'reason': string})}})
    raise ValueError('Неизвестная операция точечной доработки.')
