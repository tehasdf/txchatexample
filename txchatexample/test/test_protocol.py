import json
import mock

from twisted.internet.defer import succeed
from twisted.test.proto_helpers import StringTransport

from txchatexample.protocol import WSChatFactory


class MockChatroom(object):
    def __init__(self, log):
        self._log = log
        self._registered = False

    def getLastLog(self):
        return succeed(self._log)

    def register(self, cb):
        self._registered = True


def test_registers_on_connect():
    """When the ws connection is open, it is registered with the chatroom
    """
    talker = mock.Mock()
    chatroom = MockChatroom([])

    factory = WSChatFactory(chatroom, talker)
    proto = factory.buildProtocol(None)

    proto.onOpen()

    assert chatroom._registered


def test_sends_log_on_open():
    """When the ws client connects, we send the most recent logs to it
    """

    talker = mock.Mock()
    chatroom = MockChatroom([1, 2, 3])

    factory = WSChatFactory(chatroom, talker)
    proto = factory.buildProtocol(None)

    with mock.patch('txchatexample.protocol.ChatProtocol.sendMessage') as m:
        proto.onOpen()

    assert len(m.mock_calls) == 1

    name, args, kwargs = m.mock_calls[0]
    data = json.loads(args[0])

    assert data['action'] == 'chatLines'
    assert data['payload'] == [1, 2, 3]


def test_setName_succeed():
    """setName response is successful, if talker agrees
    """

    talker = mock.Mock()
    talker.setName.return_value = True

    factory = WSChatFactory(mock.Mock(), talker)
    proto = factory.buildProtocol(None)

    with mock.patch('txchatexample.protocol.ChatProtocol.sendMessage') as m:
        proto.handle_setName('foo')

    assert len(m.mock_calls) == 1

    name, args, kwargs = m.mock_calls[0]
    assert 'setNameSuccess' in args[0]


def test_setName_fail():
    """setName response is failed, if talker throws a ValueError
    """

    talker = mock.Mock()
    talker.setName.side_effect = ValueError()

    factory = WSChatFactory(mock.Mock(), talker)
    proto = factory.buildProtocol(None)

    with mock.patch('txchatexample.protocol.ChatProtocol.sendMessage') as m:
        proto.handle_setName('foo')

    assert len(m.mock_calls) == 1

    name, args, kwargs = m.mock_calls[0]
    assert 'setNameFailed' in args[0]


