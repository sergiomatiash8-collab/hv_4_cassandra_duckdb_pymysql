from pathlib import Path
from loguru import logger

from etl_cassandra.extract import (
    extract_campaign_daily_stats,
    extract_advertiser_spend,
    extract_user_ad_history,
    extract_user_click_stats,
    extract_advertiser_spend_by_region,
)
from etl_cassandra.transform import (
    transform_campaign_daily_stats,
    transform_advertiser_spend,
    transform_user_ad_history_chunk,
    transform_user_click_stats,
    transform_advertiser_spend_by_region,
)
from etl_cassandra.load import (
    get_cassandra_session,
    load_campaign_daily_stats,
    load_advertiser_spend,
    load_user_ad_history,
    load_user_click_stats,
    load_advertiser_spend_by_region,
)


def run():
    logger.info("Cassandra pipeline started")

    session = get_cassandra_session()

    # Query 1
    rows, columns = extract_campaign_daily_stats()
    result = transform_campaign_daily_stats(rows, columns)
    load_campaign_daily_stats(session, result)

    # Query 2
    rows = extract_advertiser_spend()
    rows = transform_advertiser_spend(rows)
    load_advertiser_spend(session, rows)

    # Query 3 — читаємо чанками бо 10M рядків
    cursor, conn = extract_user_ad_history()
    chunk_size = 50_000
    total = 0
    chunk = cursor.fetchmany(chunk_size)
    while chunk:
        converted = transform_user_ad_history_chunk(chunk)
        load_user_ad_history(session, converted)
        total += len(chunk)
        logger.info(f"user_ad_history: {total:,} rows processed")
        chunk = cursor.fetchmany(chunk_size)
    cursor.close()
    conn.close()
    logger.info(f"user_ad_history: {total:,} rows loaded")

    # Query 4
    rows = extract_user_click_stats()
    rows = transform_user_click_stats(rows)
    load_user_click_stats(session, rows)

    # Query 5
    rows = extract_advertiser_spend_by_region()
    rows = transform_advertiser_spend_by_region(rows)
    load_advertiser_spend_by_region(session, rows)

    logger.info("Cassandra pipeline finished")


if __name__ == "__main__":
    Path("logs").mkdir(exist_ok=True)
    logger.add("logs/pipeline.log", rotation="10 MB", level="INFO")
    run()