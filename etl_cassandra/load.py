from loguru import logger
from cassandra.io.asyncioreactor import AsyncioConnection
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args

# Fix для Python 3.13 на Windows — встановлюємо до створення кластера
Cluster.connection_class = AsyncioConnection


def get_cassandra_session():
    cluster = Cluster(["127.0.0.1"], port=9042, protocol_version=4)
    session = cluster.connect("adtech")
    logger.info("Connected to Cassandra")
    return session


def load_campaign_daily_stats(session, rows):
    stmt = session.prepare("""
        INSERT INTO campaign_daily_stats
        (campaign_id, day, impressions, clicks, ctr)
        VALUES (?, ?, ?, ?, ?)
    """)
    execute_concurrent_with_args(session, stmt, rows, concurrency=50)
    logger.info(f"campaign_daily_stats: {len(rows):,} rows loaded")


def load_advertiser_spend(session, rows):
    stmt = session.prepare("""
        INSERT INTO advertiser_spend
        (advertiser_id, advertiser_name, total_spend)
        VALUES (?, ?, ?)
    """)
    execute_concurrent_with_args(session, stmt, rows, concurrency=50)
    logger.info(f"advertiser_spend: {len(rows):,} rows loaded")


def load_user_ad_history(session, rows):
    stmt = session.prepare("""
        INSERT INTO user_ad_history
        (user_id, shown_at, event_id, campaign_id, campaign_name, advertiser_name, clicked)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """)
    execute_concurrent_with_args(session, stmt, rows, concurrency=50)


def load_user_click_stats(session, rows):
    stmt = session.prepare("""
        INSERT INTO user_click_stats (bucket, clicks, user_id)
        VALUES (?, ?, ?)
    """)
    execute_concurrent_with_args(session, stmt, rows, concurrency=50)
    logger.info(f"user_click_stats: {len(rows):,} rows loaded")


def load_advertiser_spend_by_region(session, rows):
    stmt = session.prepare("""
        INSERT INTO advertiser_spend_by_region
        (region, total_spend, advertiser_id, advertiser_name)
        VALUES (?, ?, ?, ?)
    """)
    execute_concurrent_with_args(session, stmt, rows, concurrency=50)
    logger.info(f"advertiser_spend_by_region: {len(rows):,} rows loaded")