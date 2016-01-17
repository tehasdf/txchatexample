from datetime import datetime
import json
import os.path
import sys
import uuid

from zope.interface import Interface, implementer

from twisted.cred.credentials import Anonymous, IAnonymous
from twisted.cred.checkers import ICredentialsChecker
from twisted.internet import reactor
from twisted.logger import Logger, textFileLogObserver, globalLogPublisher
from twisted.web.server import Site
from twisted.web.static import File
from twisted.web.proxy import ReverseProxyResource
from twisted.web.resource import Resource
from twisted.cred.portal import Portal
from twisted.internet.defer import inlineCallbacks, gatherResults, returnValue
from twisted.web.util import DeferredResource

from autobahn.twisted.resource import WebSocketResource
from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol

from txpostgres import txpostgres

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Sequence
from sqlalchemy.dialects.postgresql import dialect, TIMESTAMP
from sqlalchemy import select

from psycopg2.extras import NamedTupleCursor
from psycopg2 import IntegrityError




from sqlalchemy import bindparam
from sqlalchemy import insert


from txchatexample.db import logs, users

class ITalker(Interface):
    """
    """


@implementer(ITalker)
class Talker(object):
    def __init__(self, pool, user):
        self._pool = pool
        self._user = user

    def setName(self, name):
        query = (users
            .update()
            .where(users.c.user_id == self._user.user_id)
            .values(name=name)
            .compile(dialect=dialect())
        )
        return (self._pool.runOperation(str(query), query.params)
            .addErrback(self._onNameTaken, name)
            .addCallback(lambda _: self._refreshUser())
        )

    def _onNameTaken(self, failure, name):
        failure.trap(IntegrityError)
        raise ValueError('Name %s is already, taken' % (name, ))

    @inlineCallbacks
    def _refreshUser(self):
        query = (select([users])
            .where(users.c.user_id == self._user.user_id)
            .compile(dialect=dialect())
        )
        user = (yield self._pool.runQuery(str(query), query.params))[0]
        self._user = user
        returnValue(self._user)

    @property
    def user_id(self):
        return self._user.user_id

    def logout(self):
        pass

    def getUserDetails(self):
        return (self._refreshUser()
            .addCallback(lambda user: user._asdict())
        )


LOG_SELECT_QUERY = (select([logs, users.c.name])
    .select_from(logs.join(users))
)
class Chatroom(object):
    log = Logger()

    def __init__(self, pool):
        self._listeners = set()
        self._pool = pool

        self._listenConnection = txpostgres.Connection(self._pool.reactor)
        self._lastId = None

    def start(self):
        pool = self._pool

        return (self._listenConnection.connect(*pool.connargs, **pool.connkw)
            .addCallback(self._listenConnectionConnected)
        )

    def _listenConnectionConnected(self, conn):
        self._listenConnection.addNotifyObserver(self._onNewLineNotify)
        return self._listenConnection.runOperation('listen chat_line_notification')

    def _onNewLineNotify(self, notify):
        log_id = notify.payload
        self.log.debug('notify payload {payload}', payload=log_id)
        query = (LOG_SELECT_QUERY
            .where(logs.c.log_id == log_id)
            .compile(dialect=dialect())
        )

        return (self._pool.runQuery(str(query), query.params)
            .addCallback(self._broadcast)
        )

    def _broadcast(self, newLogs):
        newLogs = [log._asdict() for log in newLogs]

        for proto in self._listeners:
            proto.sendAction(newLogs, action='chatLines')

    def register(self, listener):
        self._listeners.add(listener)

    def unregister(self, listener):
        self._listeners.remove(listener)

    def changeName(self, from_name, to_name):
        if to_name in self._names:
            raise ValueError('Name %s is already taken' % (to_name, ))

        self._names.add(from_name)
        self._names.remove(to_name)

    def getLastLog(self):
        query = (LOG_SELECT_QUERY
            .order_by(logs.c.when.desc())
            .limit(30)
            .compile(dialect=dialect())
        )
        return (self._pool.runQuery(str(query), query.params)
            .addCallback(lambda lines: [line._asdict() for line in lines])
        )

    def say(self, user_id, line):
        query = (logs
            .insert()
            .values(user_id=user_id, text=line)
            .returning(logs.c.log_id)
            .compile(dialect=dialect())
        )
        return self._pool.runOperation(str(query), query.params)
