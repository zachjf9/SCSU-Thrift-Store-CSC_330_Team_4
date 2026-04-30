create table users (
    --Primary key
    user_id integer generated always as identity primary key,

    email varchar(255) unique not null,
    name varchar(100) not null,
    password_hash text not null);


create table profiles (
    --Primary key
    profile_id integer generated always as identity primary key,
    --Foreign key
    user_id integer unique not null,

    major varchar(100),
    bio text,

    constraint fk_profiles_users
                      foreign key (user_id)
                      references users(user_id)
                      on delete cascade);


create table listings (
    --Primary key
    listing_id integer generated always as identity primary key,
    --Foreign key
    profile_id integer not null,

    title varchar(255) not null,
    description text,
    category varchar(100),
    status boolean default true,
    image text,
    created_at timestamp default current_timestamp,

    constraint fk_listings_profiles
                      foreign key (profile_id)
                      references profiles(profile_id)
                      on delete cascade);


create table channels (
    --Primary key
    channel_id integer generated always as identity primary key,

    name varchar(100) unique not null,
    description text);


create table posts (
    --Primary key
    post_id integer generated always as identity primary key,
    --Foreign keys
    profile_id integer not null,
    channel_id integer not null,

    content text not null,
    created_at timestamp default current_timestamp,

    constraint fk_posts_profiles
                   foreign key (profile_id)
                   references profiles(profile_id)
                   on delete cascade,

    constraint fk_posts_channels
                   foreign key (channel_id)
                   references channels(channel_id)
                   on delete cascade);


create table replies (
    --Primary key
    replies_id integer generated always as identity primary key,
    --Foreign keys
    profile_id integer not null,
    post_id integer not null,

    content text not null,
    created_at timestamp default current_timestamp,

    constraint fk_replies_profiles
                     foreign key (profile_id)
                     references profiles(profile_id)
                     on delete cascade,

    constraint fk_replies_posts
                     foreign key (post_id)
                     references posts(post_id)
                     on delete cascade);

create table reviews (
    --Primary key
    review_id integer generated always as identity primary key,
    --Foreign keys
    reviewer_profile_id integer not null,
    reviewed_profile_id integer not null,

    rating integer not null,
    comment text,
    created_at timestamp default current_timestamp,

    constraint fk_reviews_reviewer
                     foreign key (reviewer_profile_id)
                     references profiles(profile_id)
                     on delete cascade,

    constraint fk_reviews_reviewed
                     foreign key (reviewed_profile_id)
                     references profiles(profile_id)
                     on delete cascade,

    constraint chk_reviews_rating
                     check (rating between 1 and 5),

    constraint chk_reviews_not_self
                     check (reviewer_profile_id <> reviews.reviewed_profile_id));

create table notifications (
    --Primary key
    notification_id integer generated always as identity primary key,
    --Foreign key
    user_id integer not null,

    message text not null,
    has_read boolean default false,
    created_at timestamp default current_timestamp,

    constraint fk_notifications_users
                           foreign key (user_id)
                           references users(user_id)
                           on delete cascade);