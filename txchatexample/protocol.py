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

from txchatexample.auth import Token
from txchatexample.chat import ITalker
from txchatexample.util import dumps

class ChatProtocol(WebSocketServerProtocol):
    log = Logger()

    def __init__(self, chatroom, talker):
        self._chatroom = chatroom
        self._talker = talker
        super(ChatProtocol, self).__init__()

    def onOpen(self):
        self._chatroom.register(self)

        (self._talker.getUserDetails()
            .addCallback(self.sendAction, action='userDetails')
        )

        (self._chatroom.getLastLog()
            .addCallback(self.sendAction, action='chatLines')
        )

    def sendAction(self, payload=None, action=None):
        self.sendMessage(dumps({
            'action': action,
            'payload': payload
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
        self.sendMessage(dumps(response))


    def handle_say(self, line):
        self._chatroom.say(user_id=self._talker.user_id, line=line)

    def onClose(self, wasClean, code, reason):
        self._chatroom.unregister(self)


class WSChatFactory(WebSocketServerFactory):
    protocol = ChatProtocol
    def __init__(self, chatroom, talker):
        self._chatroom = chatroom
        self._talker = talker
        WebSocketServerFactory.__init__(self)

    def buildProtocol(self, addr):
        proto = self.protocol(self._chatroom, self._talker)
        proto.factory = self
        return proto


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

