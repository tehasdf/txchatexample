import sys

from twisted.internet import reactor
from twisted.logger import textFileLogObserver, globalLogPublisher
from twisted.web.server import Site
from twisted.cred.portal import Portal

from txpostgres import txpostgres

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Sequence
from sqlalchemy.dialects.postgresql import dialect, TIMESTAMP
from sqlalchemy import select

from psycopg2.extras import NamedTupleCursor

from txchatexample.chat import Chatroom
from txchatexample.auth import ChatRealm, TokenChecker
from txchatexample.protocol import WSResourceWrapper
from txchatexample.web import MainResource


if __name__ == '__main__':
    pool = txpostgres.ConnectionPool(None, dbname='asdf', cursor_factory=NamedTupleCursor)
    pool.start()
    chatroom = Chatroom(pool)
    chatroom.start()
    realm = ChatRealm(pool)
    portal = Portal(realm)
    checker = TokenChecker(pool)
    portal.registerChecker(checker)
    ws = WSResourceWrapper(chatroom, portal)
    site = Site(MainResource(ws))
    reactor.listenTCP(8000, site)

    globalLogPublisher.addObserver(textFileLogObserver(sys.stdout))

    reactor.run()
