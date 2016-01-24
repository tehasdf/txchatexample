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


def getQueryWithParams(dialect, query, params):
    if hasattr(query, 'compile'):
        compiled = query.compile(dialect=dialect)
        query_params = dict(compiled.params)
        if params is not None:
            query_params.update(params)
        return str(compiled), query_params
    return query, params


class ConnectionPool(txpostgres.ConnectionPool):
    def __init__(self, **kwargs):
        kwargs.setdefault('cursor_factory', NamedTupleCursor)
        self._sqla_dialect = dialect()
        super(ConnectionPool, self).__init__(None, **kwargs)


    def runQuery(self, query, params=None):
        query, params = getQueryWithParams(self._sqla_dialect, query, params)
        return super(ConnectionPool, self).runQuery(query, params)

    def runOperation(self, query, params=None):
        query, params = getQueryWithParams(self._sqla_dialect, query, params)
        return super(ConnectionPool, self).runOperation(query, params)


class Registry(object):
    def __init__(self):
        self._registered = set()

    def register(self, other):
        self._registered.add(other)

    def unregister(self, other):
        self._registered.add(other)

    def broadcast(self, func, *args, **kwargs):
        return [func(elem, *args, **kwargs) for elem in self._registered]



class DBListener(Registry):
    def __init__(self, connection, channel='chat_line_notification'):
        super(DBListener, self).__init__()
        self._connection = connection
        self._channel = channel

    def start(self):
        self._connection.addNotifyObserver(self._onNotify)
        return self._connection.runOperation('listen %s' % (self._channel, ))

    def _onNotify(self, notify):
        self.broadcast(lambda registered: registered(notify.payload))
