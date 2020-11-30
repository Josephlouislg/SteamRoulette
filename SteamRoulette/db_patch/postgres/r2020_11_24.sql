insert into db_patch (date, version) values('2020-11-24', 0);


-- [Stetsenko]
-----------//-------------
CREATE TABLE steam_bot (
    id SERIAL NOT NULL ,
    password text NOT NULL,
    username text not NULL,
    steam_id text,
    status SMALLINT not null,
    data jsonb NOT NULL ,
    date_created TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    date_modified TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    PRIMARY KEY (id)
);

create unique index un__ix__steam_bot__username on steam_bot USING btree(username);
create unique index un__ix__steam_bot__steam_id on steam_bot USING btree(steam_id);
-----------//-------------
