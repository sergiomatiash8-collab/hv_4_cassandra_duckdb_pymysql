import os
import uuid
import duckdb
import pymysql
import pandas as pd
from loguru import logger
from dotenv import load_dotenv
from pathlib import Path
from cassandra.io.asyncioreactor import AsyncioConnection
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args

# Fix для Python 3.13 на Windows — встановлюємо до створення кластера
Cluster.connection_class = AsyncioConnection

load_dotenv()


def get_mysql_conn():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        cursorclass=pymysql.cursors.SSCursor,
    )


def get_cassandra_session():
    cluster = Cluster(["127.0.0.1"], port=9042, protocol_version=4)
    session = cluster.connect("adtech")
    logger.info("Connected to Cassandra")
    return session


def load_campaign_daily_stats(session):
    logger.info("Loading campaign_daily_stats...")

    sql = """
        SELECT
            campaign_id,
            DATE(event_timestamp)            AS day,
            COUNT(*)                         AS impressions,
            SUM(click_timestamp IS NOT NULL) AS clicks
        FROM events
        GROUP BY campaign_id, DATE(event_timestamp)
    """

    conn = get_mysql_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [d[0] for d in cursor.description]
    cursor.close()
    conn.close()

    df = pd.DataFrame(rows, columns=columns)

    duck = duckdb.connect()
    result = duck.execute("""
        SELECT
            CAST(campaign_id AS INTEGER) AS campaign_id,
            CAST(day AS DATE)            AS day,
            CAST(impressions AS BIGINT)  AS impressions,
            CAST(clicks AS BIGINT)       AS clicks,
            CASE WHEN impressions > 0
                 THEN ROUND(clicks * 1.0 / impressions, 4)
                 ELSE 0.0 END            AS ctr
        FROM df
    """).fetchall()
    duck.close()

    stmt = session.prepare("""
        INSERT INTO campaign_daily_stats
        (campaign_id, day, impressions, clicks, ctr)
        VALUES (?, ?, ?, ?, ?)
    """)

    execute_concurrent_with_args(session, stmt, result, concurrency=50)
    logger.info(f"campaign_daily_stats: {len(result):,} rows loaded")


def load_advertiser_spend(session):
    logger.info("Loading advertiser_spend...")

    sql = """
        SELECT
            a.advertiser_id,
            a.advertiser_name,
            ROUND(SUM(e.ad_cost), 2) AS total_spend
        FROM events e
        JOIN campaigns c   ON e.campaign_id   = c.campaign_id
        JOIN advertisers a ON c.advertiser_id = a.advertiser_id
        GROUP BY a.advertiser_id, a.advertiser_name
    """

    conn = get_mysql_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    stmt = session.prepare("""
        INSERT INTO advertiser_spend
        (advertiser_id, advertiser_name, total_spend)
        VALUES (?, ?, ?)
    """)

    execute_concurrent_with_args(session, stmt, rows, concurrency=50)
    logger.info(f"advertiser_spend: {len(rows):,} rows loaded")


def load_user_ad_history(session):
    logger.info("Loading user_ad_history...")

    sql = """
        SELECT
            e.user_id,
            e.event_timestamp               AS shown_at,
            e.event_id,
            e.campaign_id,
            c.campaign_name,
            a.advertiser_name,
            (e.click_timestamp IS NOT NULL) AS clicked
        FROM events e
        JOIN campaigns c   ON e.campaign_id   = c.campaign_id
        JOIN advertisers a ON c.advertiser_id = a.advertiser_id
    """

    conn = get_mysql_conn()
    cursor = conn.cursor()
    cursor.execute(sql)

    stmt = session.prepare("""
        INSERT INTO user_ad_history
        (user_id, shown_at, event_id, campaign_id, campaign_name, advertiser_name, clicked)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """)

    chunk_size = 50_000
    total = 0
    rows = cursor.fetchmany(chunk_size)

    while rows:
        converted = [
            (
                int(r[0]),
                r[1],
                uuid.UUID(r[2]),
                int(r[3]),
                r[4],
                r[5],
                bool(r[6]),
            )
            for r in rows
        ]
        execute_concurrent_with_args(session, stmt, converted, concurrency=50)
        total += len(rows)
        logger.info(f"user_ad_history: {total:,} rows processed")
        rows = cursor.fetchmany(chunk_size)

    cursor.close()
    conn.close()
    logger.info(f"user_ad_history: {total:,} rows loaded")


def load_user_click_stats(session):
    logger.info("Loading user_click_stats...")

    sql = """
        SELECT
            user_id,
            COUNT(*) AS clicks
        FROM events
        WHERE click_timestamp IS NOT NULL
        GROUP BY user_id
    """

    conn = get_mysql_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    rows_with_bucket = [(1, int(r[1]), int(r[0])) for r in rows]

    stmt = session.prepare("""
        INSERT INTO user_click_stats (bucket, clicks, user_id)
        VALUES (?, ?, ?)
    """)

    execute_concurrent_with_args(session, stmt, rows_with_bucket, concurrency=50)
    logger.info(f"user_click_stats: {len(rows):,} rows loaded")


def load_advertiser_spend_by_region(session):
    logger.info("Loading advertiser_spend_by_region...")

    sql = """
        SELECT
            e.location                   AS region,
            ROUND(SUM(e.ad_cost), 2)     AS total_spend,
            a.advertiser_id,
            a.advertiser_name
        FROM events e
        JOIN campaigns c   ON e.campaign_id   = c.campaign_id
        JOIN advertisers a ON c.advertiser_id = a.advertiser_id
        GROUP BY e.location, a.advertiser_id, a.advertiser_name
    """

    conn = get_mysql_conn()
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    stmt = session.prepare("""
        INSERT INTO advertiser_spend_by_region
        (region, total_spend, advertiser_id, advertiser_name)
        VALUES (?, ?, ?, ?)
    """)

    execute_concurrent_with_args(session, stmt, rows, concurrency=50)
    logger.info(f"advertiser_spend_by_region: {len(rows):,} rows loaded")


def load_all_cassandra():
    logger.info("Cassandra ETL started")
    session = get_cassandra_session()

    load_campaign_daily_stats(session)
    load_advertiser_spend(session)
    load_user_ad_history(session)
    load_user_click_stats(session)
    load_advertiser_spend_by_region(session)

    logger.info("Cassandra ETL finished")


if __name__ == "__main__":
    Path("logs").mkdir(exist_ok=True)
    logger.add("logs/pipeline.log", rotation="10 MB", level="INFO")
    load_all_cassandra()