create table users (
    --Primary key
    id integer generated always as identity primary key,

    email varchar(255) unique not null,
    username varchar(100) unique not null,
    password text not null,

    name varchar(100),
    major varchar(100),
    interests text,
    is_admin boolean default false,
    is_blocked boolean default false);


create table posts (
    --Primary key
    id integer generated always as identity primary key,
    --Foreign keys
    owner_id integer not null,

    title varchar(255),
    description text not null,
    category varchar(100),
    price numeric(10,2),
    condition varchar(100),
    status varchar(100),
    image text,
    created_at timestamp default current_timestamp,
    is_active boolean default true,

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

    content text not null,
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
    comment text,
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
                     check (reviews.reviewer_id <> reviews.reviewed_id));

create table notifications (
    --Primary key
    id integer generated always as identity primary key,
    --Foreign key
    user_id integer not null,

    message text not null,
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