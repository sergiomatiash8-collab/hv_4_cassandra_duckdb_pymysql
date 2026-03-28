import os
import pymysql
from loguru import logger
from dotenv import load_dotenv

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


def extract_campaign_daily_stats():
    logger.info("Extracting campaign_daily_stats from MySQL...")
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
    return rows, columns


def extract_advertiser_spend():
    logger.info("Extracting advertiser_spend from MySQL...")
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
    return rows


def extract_user_ad_history():
    logger.info("Extracting user_ad_history from MySQL...")
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
    return cursor, conn


def extract_user_click_stats():
    logger.info("Extracting user_click_stats from MySQL...")
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
    return rows


def extract_advertiser_spend_by_region():
    logger.info("Extracting advertiser_spend_by_region from MySQL...")
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
    return rows