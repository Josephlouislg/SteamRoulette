insert into db_patch (date, version) values('2020-11-19', 0);


-- [Stetsenko]
-----------//-------------
CREATE TABLE user_admin (
    id SERIAL NOT NULL,
    status SMALLINT,
    email text NOT NULL,
    password text NOT NULL,
    date_created TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    first_name text not null,
    last_name text not null,
    roles smallint[],
    PRIMARY KEY (id)
);

create unique index uc__user_admin__email on user_admin USING btree(email);

-----------//-------------
