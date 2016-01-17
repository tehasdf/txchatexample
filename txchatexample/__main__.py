import json
import os.path
import sys
import uuid

from zope.interface import Interface, implementer

from twisted.internet import reactor
from twisted.logger import Logger, textFileLogObserver, globalLogPublisher
from twisted.web.server import Site
from twisted.web.static import File
from twisted.web.proxy import ReverseProxyResource
from twisted.web.resource import Resource
from twisted.cred.portal import Portal
from twisted.internet.defer import inlineCallbacks
from twisted.web.util import DeferredResource


from autobahn.twisted.resource import WebSocketResource
from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol

from txpostgres import txpostgres

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Sequence
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy import select

from psycopg2.extras import NamedTupleCursor
from psycopg2 import IntegrityError


md = MetaData()
users = Table('chat_users', md,
    Column('user_id', Integer(), Sequence('chat_users_id_seq'), primary_key=True),
    Column('token', String(32), unique=True),
    Column('name', String(200), unique=True)
)


logs = Table('chat_logs', md,
    Column('log_id', Integer(), Sequence('chat_logs_id_seq'), primary_key=True),
    Column('user_id', Integer(), ForeignKey('chat_users')),
    Column('text', String())
)


class APIResource(Resource):
    def getChild(self, path, request):
        if path == 'ws':
            return WSResoure()
        else:
            raise NotImplementedError()


class EchoServerProtocol(WebSocketServerProtocol):
    log = Logger()

    def __init__(self, chatroom, talker):
        self._chatroom = chatroom
        self._talker = talker
        super(EchoServerProtocol, self).__init__()

    def onOpen(self):
        self.sendMessage(json.dumps({
            'action': 'userDetails',
            'payload': self._talker.getUserDetails()
        }))

    def onMessage(self, payload, isBinary):
        self.log.debug('message: {payload!r}', payload=payload)
        message = json.loads(payload)
        action = message.get('action')
        if action:
            handler = getattr(self, 'handle_%s' % (action, ), None)
            if handler:
                handler(**message.get('payload', {}))

    @inlineCallbacks
    def handle_setName(self, name):
        self.log.debug('Setting name to {name}', name=name)

        try:
            yield self._talker.setName(name)
        except ValueError:
            response = {
                'action': 'setNameFailed'
            }
        else:
            response = {
                'action': 'setNameSuccess'
            }
        self.sendMessage(json.dumps(response))


class WSChatFactory(WebSocketServerFactory):
    protocol = EchoServerProtocol
    def __init__(self, chatroom, talker):
        self._chatroom = chatroom
        self._talker = talker
        WebSocketServerFactory.__init__(self)

    def buildProtocol(self, addr):
        proto = self.protocol(self._chatroom, self._talker)
        proto.factory = self
        return proto

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

    def logout(self):
        pass

    def getUserDetails(self):
        return self._user._asdict()


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


class Chatroom(object):
    def __init__(self, pool):
        self._names = set()
        self._pool = pool

    def createRandomName(self):
        number = 0
        while True:
            nick = 'guest%d' % (number, )
            if nick not in self._names:
                self._names.add(nick)
                return nick

    def changeName(self, from_name, to_name):
        if to_name in self._names:
            raise ValueError('Name %s is already taken' % (to_name, ))

        self._names.add(from_name)
        self._names.remove(to_name)



from twisted.cred.credentials import Anonymous, IAnonymous
from twisted.cred.checkers import ICredentialsChecker


class IToken(Interface):
    pass


@implementer(IToken)
class Token(object):
    def __init__(self, value):
        self.value = value


class WSResourceWrapper(object):
    def __init__(self, chatroom, portal):
        self._chatroom = chatroom
        self._portal = portal

    def getResource(self, request):
        token = request.getCookie('token')

        if token is None:
            credentials = Anonymous()
        else:
            credentials = Token(token)

        d = (self._portal.login(credentials, None, ITalker)
            .addCallback(lambda (iface, talker, logout): WSChatFactory(self._chatroom, talker))
            .addCallback(WebSocketResource)
        )
        return DeferredResource(d)


from sqlalchemy import bindparam
from sqlalchemy import insert

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
                .addCallback(self._gotUser, token)
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

    def _gotUser(self, user, token):
        if not user:
            return self.createUser(token)
        else:
            return user[0]

    def createUser(self, token):
        query = (users
            .insert()
            .values(token=token, name=token)
            .returning(users.c.user_id)
            .compile(dialect=dialect())
        )
        self.log.debug('createUser {token}', token=token)
        return self._pool.runQuery(str(query), query.params)


class MainResource(Resource):
    def __init__(self, ws, static_path=None):
        self._ws = ws

        if static_path is None:
             static_path = os.path.join(os.path.dirname(__file__), 'static')
        self._static_path = static_path
        Resource.__init__(self)

    def _setToken(self, request):
        token = uuid.uuid4().hex
        request.addCookie('token', token)

    def getChild(self, path, request):
        token = request.getCookie('token')

        if token is None:
            self._setToken(request)

        if path == 'api':
            return APIResource()
        elif path == 'ws':
            return self._ws.getResource(request)
        else:
            return ReverseProxyResource('127.0.0.1', 8080, os.path.join('/', path))

        if not path:
            return File(os.path.join(self._static_path, 'index.html'))

        return self


if __name__ == '__main__':
    pool = txpostgres.ConnectionPool(None, dbname='asdf', cursor_factory=NamedTupleCursor)
    pool.start()
    chatroom = Chatroom(pool)
    realm = ChatRealm(pool)
    portal = Portal(realm)
    checker = TokenChecker(pool)
    portal.registerChecker(checker)
    ws = WSResourceWrapper(chatroom, portal)
    site = Site(MainResource(ws))
    reactor.listenTCP(8000, site)

    globalLogPublisher.addObserver(textFileLogObserver(sys.stdout))

    reactor.run()
