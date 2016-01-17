from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Sequence
from sqlalchemy.dialects.postgresql import TIMESTAMP

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

