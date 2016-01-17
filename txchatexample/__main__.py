import sys

from twisted.internet import reactor
from twisted.logger import textFileLogObserver, globalLogPublisher
from twisted.web.server import Site

from txpostgres import txpostgres
from psycopg2.extras import NamedTupleCursor

from txchatexample.web import makeEntryPoint

if __name__ == '__main__':
    pool = txpostgres.ConnectionPool(None, dbname='asdf', cursor_factory=NamedTupleCursor)
    pool.start()
    res = makeEntryPoint(pool)
    site = Site(res)
    reactor.listenTCP(8000, site)

    globalLogPublisher.addObserver(textFileLogObserver(sys.stdout))

    reactor.run()
