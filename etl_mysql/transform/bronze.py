from pathlib import Path
import pandas as pd
from loguru import logger

BRONZE_DIR = Path("data/bronze")
BRONZE_DIR.mkdir(parents=True, exist_ok=True)

# колонки які викидаємо з events — вони є в campaigns
EVENTS_DROP = [
    "AdvertiserName",
    "CampaignStartDate",
    "CampaignEndDate",
    "CampaignTargetingCriteria",
    "CampaignTargetingInterest",
    "CampaignTargetingCountry",
    "AdSlotSize",
    "Budget",
    "RemainingBudget",
    "WasClicked",
]

# колонки які викидаємо з campaigns
CAMPAIGNS_DROP = [
    "RemainingBudget",
]


def bronze_events(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("=== BRONZE: events (1NF) ===")
    df = df.copy()

    # викидаємо непотрібні колонки
    df = df.drop(columns=EVENTS_DROP, errors="ignore")
    logger.info(f"Колонки після drop: {df.columns.tolist()}")

    # прибираємо пробіли
    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)

    # правильні типи
    df["Timestamp"]      = pd.to_datetime(df["Timestamp"],      errors="coerce")
    df["ClickTimestamp"] = pd.to_datetime(df["ClickTimestamp"], errors="coerce")
    df["BidAmount"]      = pd.to_numeric(df["BidAmount"],       errors="coerce")
    df["AdCost"]         = pd.to_numeric(df["AdCost"],          errors="coerce")
    df["AdRevenue"]      = pd.to_numeric(df["AdRevenue"],       errors="coerce")

    # видаляємо дублі
    before = len(df)
    df = df.drop_duplicates()
    logger.info(f"Дублів видалено: {before - len(df):,}")

    # зберігаємо
    path = BRONZE_DIR / "events.parquet"
    df.to_parquet(path, index=False)
    logger.info(f"Збережено: {path} | {len(df):,} рядків")

    return df


def bronze_campaigns(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("=== BRONZE: campaigns (1NF) ===")
    df = df.copy()

    # викидаємо непотрібні колонки
    df = df.drop(columns=CAMPAIGNS_DROP, errors="ignore")
    logger.info(f"Колонки після drop: {df.columns.tolist()}")

    # прибираємо пробіли
    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)

    # правильні типи
    df["CampaignStartDate"] = pd.to_datetime(df["CampaignStartDate"], errors="coerce")
    df["CampaignEndDate"]   = pd.to_datetime(df["CampaignEndDate"],   errors="coerce")
    df["Budget"]            = pd.to_numeric(df["Budget"],             errors="coerce")

    # видаляємо дублі
    before = len(df)
    df = df.drop_duplicates()
    logger.info(f"Дублів видалено: {before - len(df):,}")

    # зберігаємо
    path = BRONZE_DIR / "campaigns.parquet"
    df.to_parquet(path, index=False)
    logger.info(f"Збережено: {path} | {len(df):,} рядків")

    return df


def bronze_users(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("=== BRONZE: users (1NF) ===")
    df = df.copy()

    # прибираємо пробіли
    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)

    # правильні типи
    df["Age"]        = pd.to_numeric(df["Age"],        errors="coerce")
    df["SignupDate"] = pd.to_datetime(df["SignupDate"], errors="coerce")

    # видаляємо дублі
    before = len(df)
    df = df.drop_duplicates()
    logger.info(f"Дублів видалено: {before - len(df):,}")

    # зберігаємо
    path = BRONZE_DIR / "users.parquet"
    df.to_parquet(path, index=False)
    logger.info(f"Збережено: {path} | {len(df):,} рядків")

    return df