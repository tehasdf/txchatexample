import json

from twisted.cred.credentials import Anonymous
from twisted.logger import Logger
from twisted.internet.defer import inlineCallbacks
from twisted.web.util import DeferredResource

from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol

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

