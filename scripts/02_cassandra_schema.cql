-- Keyspace
CREATE KEYSPACE IF NOT EXISTS adtech
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE adtech;

-- Query 1: CTR per campaign per day
CREATE TABLE IF NOT EXISTS campaign_daily_stats (
    campaign_id   int,
    day           date,
    impressions   bigint,
    clicks        bigint,
    ctr           double,
    PRIMARY KEY (campaign_id, day)
) WITH CLUSTERING ORDER BY (day DESC);

-- Query 2: Top advertisers by spend
CREATE TABLE IF NOT EXISTS advertiser_spend (
    advertiser_id   int,
    advertiser_name text,
    total_spend     double,
    PRIMARY KEY (advertiser_id)
);

-- Query 3: User ad history
CREATE TABLE IF NOT EXISTS user_ad_history (
    user_id         int,
    shown_at        timestamp,
    event_id        uuid,
    campaign_id     int,
    campaign_name   text,
    advertiser_name text,
    clicked         boolean,
    PRIMARY KEY (user_id, shown_at, event_id)
) WITH CLUSTERING ORDER BY (shown_at DESC, event_id ASC);

-- Query 4: Top users by clicks
CREATE TABLE IF NOT EXISTS user_click_stats (
    bucket    int,
    clicks    bigint,
    user_id   int,
    PRIMARY KEY (bucket, clicks, user_id)
) WITH CLUSTERING ORDER BY (clicks DESC, user_id ASC);

-- Query 5: Top advertisers by region
CREATE TABLE IF NOT EXISTS advertiser_spend_by_region (
    region          text,
    total_spend     double,
    advertiser_id   int,
    advertiser_name text,
    PRIMARY KEY (region, total_spend, advertiser_id)
) WITH CLUSTERING ORDER BY (total_spend DESC, advertiser_id ASC);