import os.path
import uuid

from twisted.web.static import File
from twisted.web.proxy import ReverseProxyResource
from twisted.web.resource import Resource
from twisted.web.util import DeferredResource

from autobahn.twisted.resource import WebSocketResource

from txchatexample.auth import makePortal, Token
from txchatexample.chat import Chatroom, ITalker
from txchatexample.protocol import WSChatFactory
from txchatexample.util import DBListener


class APIResource(Resource):
    def getChild(self, path, request):
        if path == 'ws':
            return WSResoure()
        else:
            raise NotImplementedError()


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


def makeEntryPoint(pool, conn):
    db_listener = DBListener(conn)
    chatroom = Chatroom(pool, db_listener)
    chatroom.start()

    portal = makePortal(pool)

    ws = WSResourceWrapper(chatroom, portal)
    return MainResource(ws)
