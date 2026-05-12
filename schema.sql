create table users (
    --Primary key
    id integer generated always as identity primary key,

    email varchar(150) unique not null,
    username varchar(150) unique not null,
    password varchar(150) not null,

    name varchar(150),
    major varchar(150),
    interests varchar(300),
    image varchar(200),

    is_admin boolean default false,
    is_blocked boolean default false);


create table posts (
    --Primary key
    id integer generated always as identity primary key,
    --Foreign keys
    owner_id integer not null,

    title varchar(150) not null,
    description varchar(300) not null,
    category varchar(80),
    price numeric(10,2),
    condition varchar(80),
    status varchar(80),
    image varchar(200),
    is_active boolean default true,
    created_at timestamp default current_timestamp,

    constraint fk_posts_owner
                   foreign key (owner_id)
                   references users(id)
                   on delete cascade);


create table messages (
    --Primary key
    id integer generated always as identity primary key,
    --Foreign keys
    sender_id integer not null,
    receiver_id integer not null,

    content varchar(500) not null,
    created_at timestamp default current_timestamp,

    constraint fk_messages_sender
                     foreign key (sender_id)
                     references users(id)
                     on delete cascade,

    constraint fk_messages_receiver
                     foreign key (receiver_id)
                     references users(id)
                     on delete cascade);

create table reviews (
    --Primary key
    id integer generated always as identity primary key,
    --Foreign keys
    reviewer_id integer not null,
    reviewed_id integer not null,

    rating integer not null,
    comment varchar(300),
    created_at timestamp default current_timestamp,

    constraint fk_reviews_reviewer
                     foreign key (reviewer_id)
                     references users(id)
                     on delete cascade,

    constraint fk_reviews_reviewed
                     foreign key (reviewed_id)
                     references users(id)
                     on delete cascade,

    constraint chk_reviews_rating
                     check (rating between 1 and 5),

    constraint chk_reviews_not_self
                     check (reviewer_id <> reviewed_id));

create table notifications (
    --Primary key
    id integer generated always as identity primary key,
    --Foreign key
    user_id integer not null,

    message varchar(300) not null,
    is_read boolean default false,
    created_at timestamp default current_timestamp,

    constraint fk_notifications_user
                           foreign key (user_id)
                           references users(id)
                           on delete cascade);

create table favorites (
    --Primary key
    id integer generated always as identity primary key,
    --Foreign key
    user_id integer not null,
    post_id integer not null,

    created_at timestamp default current_timestamp,

    constraint fk_favorites_user
                       foreign key (user_id)
                       references users(id)
                       on delete cascade,

    constraint fk_favorites_post
                       foreign key (post_id)
                       references posts(id)
                       on delete cascade,

    constraint unique_favorite
                       unique (user_id, post_id));

create table reports (
    --Primary key
    id integer generated always as identity primary key,
    --Foreign key
    reporter_id integer not null,
    reported_user_id integer,
    post_id integer,

    reason varchar(500) not null,
    status varchar(50) default 'Open',
    created_at timestamp default current_timestamp,

    constraint fk_reports_reporter
                     foreign key (reporter_id)
                     references users(id)
                     on delete cascade,

    constraint fk_reports_reported
                     foreign key (reported_user_id)
                     references users(id)
                     on delete cascade,

    constraint fk_reports_post
                     foreign key (post_id)
                     references posts(id)
                     on delete cascade,

    constraint chk_reports_target
                     check (reported_user_id is not null or post_id is not null));