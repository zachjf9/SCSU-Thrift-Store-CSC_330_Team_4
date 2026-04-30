create table users (
    user_id integer generated always as identity primary key,
    email varchar(255) unique not null,
    name varchar(100) not null,
    password_hash text not null
);

create table profiles (
    profile_id integer generated always as identity primary key,
    user_id integer unique not null,

    major varchar(100),
    bio text,

    constraint fk_profiles_user
                      foreign key (user_id)
                      references users(user_id)
                      on delete cascade
);