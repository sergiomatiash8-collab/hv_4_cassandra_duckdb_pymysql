from pathlib import Path
import pandas as pd
from loguru import logger

BRONZE_DIR = Path("data/bronze")
SILVER_DIR = Path("data/silver")
SILVER_DIR.mkdir(parents=True, exist_ok=True)


def silver_events(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("=== SILVER: events (2NF) ===")
    df = df.copy()

    # перевіряємо що залишились правильні колонки
    expected = [
        "EventID", "CampaignName", "UserID", "Device",
        "Location", "Timestamp", "BidAmount", "AdCost",
        "AdRevenue", "ClickTimestamp"
    ]
    missing = [col for col in expected if col not in df.columns]
    if missing:
        logger.warning(f"Відсутні колонки: {missing}")

    # видаляємо рядки без EventID і CampaignName — без них рядок безглуздий
    before = len(df)
    df = df.dropna(subset=["EventID", "CampaignName", "UserID"])
    logger.info(f"Видалено рядків без ключів: {before - len(df):,}")

    # зберігаємо
    path = SILVER_DIR / "events.parquet"
    df.to_parquet(path, index=False)
    logger.info(f"Збережено: {path} | {len(df):,} рядків")

    return df


def silver_campaigns(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("=== SILVER: campaigns (2NF) ===")
    df = df.copy()

    # видаляємо рядки без CampaignID і CampaignName
    before = len(df)
    df = df.dropna(subset=["CampaignID", "CampaignName"])
    logger.info(f"Видалено рядків без ключів: {before - len(df):,}")

    # зберігаємо
    path = SILVER_DIR / "campaigns.parquet"
    df.to_parquet(path, index=False)
    logger.info(f"Збережено: {path} | {len(df):,} рядків")

    return df


def silver_users(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("=== SILVER: users (2NF) ===")
    df = df.copy()

    # видаляємо рядки без UserID
    before = len(df)
    df = df.dropna(subset=["UserID"])
    logger.info(f"Видалено рядків без ключів: {before - len(df):,}")

    # зберігаємо
    path = SILVER_DIR / "users.parquet"
    df.to_parquet(path, index=False)
    logger.info(f"Збережено: {path} | {len(df):,} рядків")

    return df