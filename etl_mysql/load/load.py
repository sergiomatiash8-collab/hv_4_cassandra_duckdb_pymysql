from pathlib import Path
import pandas as pd
import polars as pl
import mysql.connector
from sqlalchemy import create_engine
from loguru import logger
from dotenv import load_dotenv
import os

load_dotenv()

GOLD_DIR = Path("data/gold")


EVENTS_COLUMNS = [
    "event_id", "campaign_id", "user_id", "device", "location",
    "event_timestamp", "bid_amount", "ad_cost", "ad_revenue", "click_timestamp"
]


def get_engine():
    host     = os.getenv("DB_HOST")
    port     = os.getenv("DB_PORT")
    name     = os.getenv("DB_NAME")
    user     = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
    engine = create_engine(url)
    logger.info(f"Підключення до бази: {host}:{port}/{name}")
    return engine


def get_connector():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        allow_local_infile=True,
    )


def load_table_pandas(df: pd.DataFrame, table_name: str, engine) -> None:
    logger.info(f"Завантажуємо {table_name}: {len(df):,} рядків...")
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=10000,
    )
    logger.info(f"{table_name} завантажено ✅")


# ── ПОВІЛЬНО  ──────────────────────────────────────────────────
# def load_table_polars(parquet_path, table_name, engine):
#     """Працює але повільно — ~3-4 години для 10 млн рядків"""
#     df = pl.read_parquet(parquet_path)
#     total = len(df)
#     chunk_size = 50_000
#     for i in range(0, total, chunk_size):
#         chunk = df.slice(i, chunk_size).to_pandas()
#         chunk.to_sql(name=table_name, con=engine,
#                      if_exists="append", index=False, chunksize=50_000)
#         logger.info(f"  {table_name}: {min(i+chunk_size, total):,} / {total:,}")
# ─────────────────────────────────────────────────────────────────────────────


def load_events_fast(parquet_path: Path) -> None:
    """Швидке завантаження через mysql-connector + executemany + вимкнені індекси"""
    logger.info("Завантажуємо events через mysql-connector (швидкий метод)...")

    conn = get_connector()
    cursor = conn.cursor()

    # вимикаємо FK і індекси для швидкості
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("SET UNIQUE_CHECKS = 0;")
    cursor.execute("SET autocommit = 0;")

  
    df = pl.read_parquet(parquet_path).select(EVENTS_COLUMNS)
    total = len(df)
    chunk_size = 100_000

    sql = """
        INSERT INTO events
            (event_id, campaign_id, user_id, device, location,
             event_timestamp, bid_amount, ad_cost, ad_revenue, click_timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    for i in range(0, total, chunk_size):
        chunk = df.slice(i, chunk_size)
        rows = list(chunk.iter_rows())
        cursor.executemany(sql, rows)
        conn.commit()
        logger.info(f"  events: {min(i + chunk_size, total):,} / {total:,}")

   
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    cursor.execute("SET UNIQUE_CHECKS = 1;")
    cursor.execute("SET autocommit = 1;")
    conn.commit()
    cursor.close()
    conn.close()
    logger.info("events завантажено ✅")


def load_all(advertisers, campaigns, users, events) -> None:
    engine = get_engine()
    load_table_pandas(advertisers, "advertisers", engine)
    load_table_pandas(users,       "users",       engine)
    load_table_pandas(campaigns,   "campaigns",   engine)
    load_events_fast(GOLD_DIR / "events.parquet")