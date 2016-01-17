from datetime import datetime
import json

from psycopg2.extras import NamedTupleCursor
from sqlalchemy.dialects.postgresql import dialect

from txpostgres import txpostgres


class JSONEncoderWithDatetime(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return super(JSONEncoderWithDatetime, self).default(obj)


def dumps(obj, encoder=JSONEncoderWithDatetime()):
    return encoder.encode(obj)


class ConnectionPool(txpostgres.ConnectionPool):
    def __init__(self, **kwargs):
        kwargs.setdefault('cursor_factory', NamedTupleCursor)
        self._sqla_dialect = dialect()
        super(ConnectionPool, self).__init__(None, **kwargs)

    def _getQueryWithParams(self, query, params):
        if hasattr(query, 'compile'):
            compiled = query.compile(dialect=self._sqla_dialect)
            query_params = dict(compiled.params)
            if params is not None:
                query_params.update(params)
            return str(compiled), query_params
        return query, params

    def runQuery(self, query, params=None):
        query, params = self._getQueryWithParams(query, params)
        return super(ConnectionPool, self).runQuery(query, params)

    def runOperation(self, query, params=None):
        query, params = self._getQueryWithParams(query, params)
        return super(ConnectionPool, self).runOperation(query, params)
