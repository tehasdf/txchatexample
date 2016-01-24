from zope.interface import Interface, implementer, Attribute

from twisted.logger import Logger
from twisted.internet.defer import inlineCallbacks, returnValue

from txpostgres import txpostgres

from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy import select

from psycopg2 import IntegrityError

from txchatexample.db import logs, users
from txchatexample.util import Registry


class ITalker(Interface):
    """
    """
    user_id = Attribute('user_id')

    def logout():
        pass

    def getUserDetails():
        """Get some user info from the database"""

    def setName(name):
        """Call this to trigger a name change in the db"""


@implementer(ITalker)
class Talker(object):
    """An object representing a single chatroom user.

    This is the application-layer "avatar", that is used from the
    communication-layer protocol.
    While a protocol represents a connection, the avatar represents a user.
    """
    def __init__(self, pool, user):
        self._pool = pool
        self._user = user

    def setName(self, name):
        query = (users
            .update()
            .where(users.c.user_id == self._user.user_id)
            .values(name=name)
        )
        return (self._pool.runOperation(query)
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
        )
        user = (yield self._pool.runQuery(query))[0]
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
class Chatroom(Registry):
    log = Logger()

    def __init__(self, pool, listener):
        super(Chatroom, self).__init__()
        self._dbListener = listener
        self._pool = pool

    def start(self):
        self.log.info('Starting')
        self._dbListener.register(self._onNewLineNotify)
        return self._dbListener.start()

    def _onNewLineNotify(self, log_id):
        self.log.debug('notify payload {payload}', payload=log_id)
        query = (LOG_SELECT_QUERY
            .where(logs.c.log_id == log_id)
        )

        return (self._pool.runQuery(query)
            .addCallback(lambda logs: [log._asdict() for log in logs])
            .addCallback(lambda logs: self.broadcast(self._sendLogs, logs))
        )

    def _sendLogs(self, proto, logs):
        proto.sendAction(logs, action='chatLines')

    def changeName(self, from_name, to_name):
        if to_name in self._names:
            raise ValueError('Name %s is already taken' % (to_name, ))

        self._names.add(from_name)
        self._names.remove(to_name)

    def getLastLog(self):
        query = (LOG_SELECT_QUERY
            .order_by(logs.c.when.desc())
            .limit(30)
        )
        return (self._pool.runQuery(query)
            .addCallback(lambda lines: [line._asdict() for line in lines])
        )

    def say(self, user_id, line):
        query = (logs
            .insert()
            .values(user_id=user_id, text=line)
            .returning(logs.c.log_id)
        )
        return self._pool.runOperation(query)
