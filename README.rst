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

Some patterns shown by this code:

* sqlalchemy core usage
* registry+callbacks
* txpostgres listen/notify
* the new twisted.log logger
* twisted.cred usage (with twisted.web)


Live demo
----------

https://trewq.pl/chat



Running the code
----------------

To run the tests, use `py.test txchatexample`

Install it into your virtualenv (eg. with a `python setup.py develop`),
and simply run `python -m txchatexample`. To run the frontend project,
go to the `frontend` directory and do `npm run dev`. Point your browser to
http://localhost:8000, so that requests to the frontend devserver are proxied
by the twisted server (so there's no need for CORS).


Deployment
----------

To deploy an app like this, simply run the program like usual, and use nginx
to proxy http requests to it.


TODO
----

* add more tests
* migrate with alembic