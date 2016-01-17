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

from txchatexample.db import users
from txchatexample.chat import ITalker, Talker

class IToken(Interface):
    pass


@implementer(IToken)
class Token(object):
    def __init__(self, value):
        self.value = value

@implementer(ICredentialsChecker)
class TokenChecker(object):
    credentialInterfaces = [IToken]
    log = Logger()

    def __init__(self, pool):
        self._pool = pool

    def requestAvatarId(self, credentials):
        if IToken.providedBy(credentials):
            token = credentials.value

            return (self.getUserByToken(token)
                .addCallback(self._createIfNotExists, token)
                .addCallback(lambda users: users[0])
                .addCallback(lambda user: user.user_id)
            )

        else:
            raise NotImplementedError()

    def getUserByToken(self, token):
        self.log.debug('getUserByToken {token}', token=token)
        query = (select([users.c.user_id])
            .where(users.c.token == token)
            .compile(dialect=dialect())
        )
        return self._pool.runQuery(str(query), query.params)

    def _createIfNotExists(self, user, token):
        if not user:
            return self.createUser(token)
        else:
            return user

    def createUser(self, token):
        query = (users
            .insert()
            .values(token=token, name=token)
            .returning(users.c.user_id)
            .compile(dialect=dialect())
        )
        self.log.debug('createUser {query.params}', query=query)
        return self._pool.runQuery(str(query), query.params)

class ChatRealm(object):
    log = Logger()

    def __init__(self, pool):
        self._pool = pool

    def requestAvatar(self, avatarId, mind, *ifaces):
        self.log.debug('requestAvatar {avatarId}', avatarId=avatarId)

        for iface in ifaces:
            if iface is ITalker:
                return (self._makeTalker(avatarId)
                    .addCallback(lambda talker: (ITalker, talker, talker.logout))
                )
        else:
            raise ValueError('Can only return ITalker, requested %s' % (ifaces, ))

    def _makeTalker(self, avatarId):
        return (self._getUser(avatarId)
            .addCallback(lambda user: Talker(self._pool, user))
        )

    def _getUser(self, user_id):
        query = (select([users])
            .where(users.c.user_id == user_id)
            .compile(dialect=dialect())
        )
        return (self._pool.runQuery(str(query), query.params)
            .addCallback(lambda users: users[0])
        )