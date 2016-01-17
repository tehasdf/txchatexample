import sys

from twisted.internet import reactor
from twisted.logger import textFileLogObserver, globalLogPublisher
from twisted.web.server import Site

from txchatexample.web import makeEntryPoint
from txchatexample.util import ConnectionPool


if __name__ == '__main__':
    pool = ConnectionPool(dbname='asdf')
    pool.start()

    res = makeEntryPoint(pool)
    site = Site(res)
    reactor.listenTCP(8000, site)

    globalLogPublisher.addObserver(textFileLogObserver(sys.stdout))

    reactor.run()
