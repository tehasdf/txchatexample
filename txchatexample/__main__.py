import json
import os.path
import sys
import uuid

from twisted.internet import reactor
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File
from twisted.web.proxy import ReverseProxyResource
from twisted.web.resource import Resource

from autobahn.twisted.resource import WebSocketResource
from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol

from txpostgres import txpostgres

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey

md = MetaData()
users = Table('chat_users', md,
    Column('user_id', Integer(), primary_key=True),
    Column('token', String(32), unique=True),
    Column('name', String(200), unique=True)
)


logs = Table('chat_logs', md,
    Column('log_id', Integer(), primary_key=True),
    Column('user_id', Integer(), ForeignKey('chat_users')),
    Column('text', String())
)
from sqlalchemy.dialects.postgresql import dialect


from sqlalchemy import select





class APIResource(Resource):
    def getChild(self, path, request):
        if path == 'ws':
            return WSResoure()
        else:
            raise NotImplementedError()


class EchoServerProtocol(WebSocketServerProtocol):
    def __init__(self, talker):
        self._talker = talker
        super(EchoServerProtocol, self).__init__()

    def onOpen(self):

        self.sendMessage(json.dumps({'a': 'b'}))

    def onMessage(self, payload, isBinary):
        self.sendMessage(payload, isBinary)


class WSChatFactory(WebSocketServerFactory):
    protocol = EchoServerProtocol
    def __init__(self, talker):
        self._talker = talker
        WebSocketServerFactory.__init__(self)

    def buildProtocol(self, addr):
        proto = self.protocol(self._talker)
        proto.factory = self
        return proto

from twisted.cred.portal import Portal

from zope.interface import Interface, implementer
from twisted.web.util import DeferredResource

class ITalker(Interface):
    """
    """

@implementer(ITalker)
class Talker(object):
    def __init__(self, chatroom, id):
        self._chatroom = chatroom
        self._id = id
        self.name = id

    def logout(self):
        pass

class ChatRealm(object):
    def __init__(self, chatroom):
        self._chatroom = chatroom

    def requestAvatar(self, avatarId, mind, *ifaces):
        for iface in ifaces:
            if iface is ITalker:
                talker = Talker(chatroom, avatarId)
                return (ITalker, talker, talker.logout)
        else:
            raise ValueError('Can only return ITalker, requested %s' % (ifaces, ))



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
    def __init__(self, portal):
        self._portal = portal

    def getResource(self, request):
        token = request.getCookie('token')
        if token is None:
            credentials = Anonymous()
        else:
            credentials = Token(token)
        d = (self._portal.login(credentials, None, ITalker)
            .addCallback(lambda (iface, talker, logout): WSChatFactory(talker))
            .addCallback(WebSocketResource)
        )
        return DeferredResource(d)


@implementer(ICredentialsChecker)
class TokenChecker(object):
    credentialInterfaces = [IAnonymous, IToken]
    def __init__(self, pool):
        self._pool = pool

    def requestAvatarId(self, credentials):
        if IAnonymous.providedBy(credentials):
            return ''

        elif IToken.providedBy(credentials):
            return credentials.value



class MainResource(Resource):
    def __init__(self, ws, static_path=None):
        self._ws = ws

        if static_path is None:
             static_path = os.path.join(os.path.dirname(__file__), 'static')
        self._static_path = static_path
        Resource.__init__(self)

    def _setToken(self, request):
        token = uuid.uuid4().hex
        request.addCookie('token', 'chuj')

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
    pool = txpostgres.ConnectionPool(None, dbname='asdf')
    pool.start()
    chatroom = Chatroom(pool)
    realm = ChatRealm(chatroom)
    portal = Portal(realm)
    checker = TokenChecker(pool)
    portal.registerChecker(checker)
    ws = WSResourceWrapper(portal)
    log.startLogging(sys.stdout)
    site = Site(MainResource(ws))
    reactor.listenTCP(8000, site)
    reactor.run()
