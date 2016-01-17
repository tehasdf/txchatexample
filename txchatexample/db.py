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

md = MetaData()

chat_users_id_seq = Sequence('chat_users_id_seq')

users = Table('chat_users', md,
    Column('user_id', Integer(), chat_users_id_seq, primary_key=True),
    Column('token', String(32), unique=True),
    Column('name', String(200), unique=True)
)


chat_logs_seq = Sequence('chat_logs_id_seq')

logs = Table('chat_logs', md,
    Column('log_id', Integer(), chat_logs_seq,
        server_default=chat_logs_seq.next_value(), primary_key=True),
    Column('user_id', Integer(), ForeignKey('chat_users')),
    Column('when', TIMESTAMP(timezone=False)),
    Column('text', String())
)

