create sequence chat_users_id_seq;

create table chat_users (
    user_id integer primary key default nextval('chat_users_id_seq'),
    token varchar(32) unique,
    name varchar(200) unique
);

create sequence chat_logs_id_seq;

create table chat_logs (
    log_id integer primary key default nextval('chat_logs_id_seq'),
    user_id integer references chat_users,
    "when" timestamp without time zone default (now() at time zone 'utc'),
    text varchar(2000)
);



create or replace function chat_line_notify() returns trigger as $$
    begin
        perform pg_notify('chat_line_notification', NEW.log_id::text);
        return new;
    end;
$$ language plpgsql;

create trigger chat_line_trigger
    after insert on chat_logs
    for each row
    execute procedure chat_line_notify();
