import sys

from twisted.logger import textFileLogObserver, globalLogPublisher
from twisted.web.server import Site
from twisted.internet.task import react
from twisted.internet.endpoints import serverFromString
from twisted.internet.defer import gatherResults, inlineCallbacks, Deferred

from psycopg2.extras import NamedTupleCursor
from txpostgres import txpostgres

from txchatexample.util import ConnectionPool
from txchatexample.web import makeEntryPoint


@inlineCallbacks
def main(reactor, server='tcp:8000'):
    pool = ConnectionPool(dbname='asdf')
    conn = txpostgres.Connection()
    yield gatherResults([
        pool.start(),
        conn.connect(dbname='asdf', cursor_factory=NamedTupleCursor)
    ])

    res = yield makeEntryPoint(pool, conn)
    site = Site(res)

    ep = serverFromString(reactor, server)
    ep.listen(site)
    yield Deferred() # wait forever


if __name__ == '__main__':
    globalLogPublisher.addObserver(textFileLogObserver(sys.stdout))
    react(main)
