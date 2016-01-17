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

