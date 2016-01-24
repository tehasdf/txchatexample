txchatexample
=============

This is a simple example project so I have something to point people to, when
describing some twisted python patterns ;)

It's a web-based chat application, that saves the incoming messages to the
database, and uses postgresql's listen/notify to broadcast it to the other
users.

DB queries are realized using txpostgres, by constructing them with sqlalchemy
core and rendering them to strings. It does NOT use the sqlalchemy orm.

Frontend is realized as a react-redux app.

Connectivity is websockets with autobahn.

Running the code
----------------

Install it into your virtualenv, and simply run `python -m txchatexample`.