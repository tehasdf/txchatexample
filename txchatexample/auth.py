"""This implements twisted.cred for the chat application.

The Portal gets credentials from the application (eg. from a cookie; here: token)
and passes it to the checkers; checkers validate the credentials, and if
the credentials are correct, a avatar id (user id) is returned. The avatar id
is then passed to the Realm, which returns an avatar (a "user object";
here: ITalker).

The TokenChecker does a simple database lookup to get the user id, based on the
token.

For usage, see txchatexample/web.py, WSResourceWrapper.getResource
"""

from zope.interface import Interface, implementer

from twisted.cred.checkers import ICredentialsChecker
from twisted.cred.portal import Portal
from twisted.logger import Logger

from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy import select

from txchatexample.db import users
from txchatexample.chat import ITalker, Talker


class IToken(Interface):
    pass


@implementer(IToken)
class Token(object):
    def __init__(self, value):
        self.value = value


@implementer(ICredentialsChecker)
class TokenChecker(object):
    credentialInterfaces = [IToken]
    log = Logger()

    def __init__(self, pool):
        self._pool = pool

    def requestAvatarId(self, credentials):
        if IToken.providedBy(credentials):
            token = credentials.value

            return (self.getUserByToken(token)
                .addCallback(self._createIfNotExists, token)
                .addCallback(lambda users: users[0])
                .addCallback(lambda user: user.user_id)
            )

        else:
            raise NotImplementedError()

    def getUserByToken(self, token):
        self.log.debug('getUserByToken {token}', token=token)
        query = (select([users.c.user_id])
            .where(users.c.token == token)
        )
        return self._pool.runQuery(query)

    def _createIfNotExists(self, user, token):
        if not user:
            return self.createUser(token)
        else:
            return user

    def createUser(self, token):
        query = (users
            .insert()
            .values(token=token, name=token)
            .returning(users.c.user_id)
        )
        self.log.debug('createUser {token}', token=token)
        return self._pool.runQuery(query)


class ChatRealm(object):
    log = Logger()

    def __init__(self, pool):
        self._pool = pool

    def requestAvatar(self, avatarId, mind, *ifaces):
        self.log.debug('requestAvatar {avatarId}', avatarId=avatarId)

        for iface in ifaces:
            if iface is ITalker:
                return (self._makeTalker(avatarId)
                    .addCallback(lambda talker: (ITalker, talker, talker.logout))
                )
        else:
            raise ValueError('Can only return ITalker, requested %s' % (ifaces, ))

    def _makeTalker(self, avatarId):
        return (self._getUser(avatarId)
            .addCallback(lambda user: Talker(self._pool, user))
        )

    def _getUser(self, user_id):
        query = (select([users])
            .where(users.c.user_id == user_id)
        )
        return (self._pool.runQuery(query)
            .addCallback(lambda users: users[0])
        )


def makePortal(pool):
    realm = ChatRealm(pool)
    portal = Portal(realm)
    checker = TokenChecker(pool)
    portal.registerChecker(checker)
    return portal
