insert into db_patch (date, version) values('2020-11-22', 0);


-- [Stetsenko]
-----------//-------------
CREATE TABLE auth_user_session (
    status SMALLINT not null ,
    session_key text NOT NULL,
    user_ident text,
    client_name text,
    remote_addr text,
    data jsonb,
    creation_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    expiration_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    device_type SMALLINT not null,
    PRIMARY KEY (session_key)
);

create index ix__auth_user_session__expiration_time on auth_user_session USING btree(expiration_time);

-----------//-------------
