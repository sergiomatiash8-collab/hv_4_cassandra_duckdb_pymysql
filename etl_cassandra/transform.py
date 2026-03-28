import uuid
import duckdb
import pandas as pd
from loguru import logger


def transform_campaign_daily_stats(rows, columns):
    logger.info("Transforming campaign_daily_stats...")
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
    logger.info(f"campaign_daily_stats: {len(result):,} rows transformed")
    return result


def transform_advertiser_spend(rows):
    logger.info("Transforming advertiser_spend...")
    # дані вже агреговані в MySQL — просто повертаємо як є
    return rows


def transform_user_ad_history_chunk(rows):
    # конвертуємо типи для Cassandra
    return [
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


def transform_user_click_stats(rows):
    logger.info("Transforming user_click_stats...")
    # додаємо bucket=1 щоб зібрати всіх юзерів в один partition
    return [(1, int(r[1]), int(r[0])) for r in rows]


def transform_advertiser_spend_by_region(rows):
    logger.info("Transforming advertiser_spend_by_region...")
    # дані вже агреговані в MySQL — просто повертаємо як є
    return rows