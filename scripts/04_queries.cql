-- Query 1: CTR per campaign per day
SELECT campaign_id, day, impressions, clicks, ctr
FROM campaign_daily_stats
WHERE campaign_id = 387
ORDER BY day DESC;

-- Query 2: Top 5 advertisers by total spend
SELECT advertiser_name, total_spend
FROM advertiser_spend
LIMIT 5;

-- Query 3: Last 10 ads for a user
SELECT shown_at, campaign_name, advertiser_name, clicked
FROM user_ad_history
WHERE user_id = 617250
ORDER BY shown_at DESC
LIMIT 10;

-- Query 4: Top 10 users by clicks
SELECT user_id, clicks
FROM user_click_stats
WHERE bucket = 1
ORDER BY clicks DESC
LIMIT 10;

-- Query 5: Top 5 advertisers by region
SELECT advertiser_name, total_spend
FROM advertiser_spend_by_region
WHERE region = 'USA'
LIMIT 5;