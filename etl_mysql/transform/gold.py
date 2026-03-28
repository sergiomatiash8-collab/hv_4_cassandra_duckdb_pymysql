from pathlib import Path
import pandas as pd
import re
from loguru import logger

SILVER_DIR = Path("data/silver")
GOLD_DIR   = Path("data/gold")
GOLD_DIR.mkdir(parents=True, exist_ok=True)


def gold_advertisers(campaigns: pd.DataFrame) -> pd.DataFrame:
    logger.info("=== GOLD: advertisers (3NF) ===")

    advertisers = (
        campaigns[["AdvertiserName"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    advertisers.insert(0, "advertiser_id", range(1, len(advertisers) + 1))
    advertisers.rename(columns={"AdvertiserName": "advertiser_name"}, inplace=True)

    path = GOLD_DIR / "advertisers.parquet"
    advertisers.to_parquet(path, index=False)
    logger.info(f"Збережено: {path} | {len(advertisers):,} рядків")

    return advertisers


def _parse_targeting(criteria: str):
    """Розбиває 'Age 24-42, Gaming, India' на окремі поля"""
    if pd.isna(criteria):
        return None, None, None, None
    age_match = re.search(r'Age (\d+)-(\d+)', str(criteria))
    age_min = int(age_match.group(1)) if age_match else None
    age_max = int(age_match.group(2)) if age_match else None
    parts = [p.strip() for p in str(criteria).split(',')]
    interest = parts[1] if len(parts) > 1 else None
    country  = parts[2] if len(parts) > 2 else None
    return age_min, age_max, interest, country


def gold_campaigns(campaigns: pd.DataFrame, advertisers: pd.DataFrame) -> pd.DataFrame:
    logger.info("=== GOLD: campaigns (3NF) ===")
    df = campaigns.copy()

    # замінюємо AdvertiserName на advertiser_id
    name_to_id = advertisers.set_index("advertiser_name")["advertiser_id"].to_dict()
    df["advertiser_id"] = df["AdvertiserName"].map(name_to_id)
    df = df.drop(columns=["AdvertiserName"])

    # розбиваємо targeting_criteria на окремі колонки (3NF)
    parsed = df["TargetingCriteria"].apply(
        lambda x: pd.Series(
            _parse_targeting(x),
            index=["targeting_age_min", "targeting_age_max",
                   "targeting_interest", "targeting_country"]
        )
    )
    df = pd.concat([df, parsed], axis=1)
    df = df.drop(columns=["TargetingCriteria"])

    # перейменовуємо колонки
    df.rename(columns={
        "CampaignID":        "campaign_id",
        "CampaignName":      "campaign_name",
        "CampaignStartDate": "start_date",
        "CampaignEndDate":   "end_date",
        "AdSlotSize":        "ad_slot_size",
        "Budget":            "budget",
    }, inplace=True)

    # впорядковуємо колонки
    df = df[[
        "campaign_id", "advertiser_id", "campaign_name",
        "start_date", "end_date",
        "targeting_age_min", "targeting_age_max",
        "targeting_interest", "targeting_country",
        "ad_slot_size", "budget"
    ]]

    path = GOLD_DIR / "campaigns.parquet"
    df.to_parquet(path, index=False)
    logger.info(f"Збережено: {path} | {len(df):,} рядків")

    return df


def gold_users(users: pd.DataFrame) -> pd.DataFrame:
    logger.info("=== GOLD: users (3NF) ===")
    df = users.copy()

    df.rename(columns={
        "UserID":     "user_id",
        "Age":        "age",
        "Gender":     "gender",
        "Location":   "location",
        "Interests":  "interests",
        "SignupDate": "signup_date",
    }, inplace=True)

    path = GOLD_DIR / "users.parquet"
    df.to_parquet(path, index=False)
    logger.info(f"Збережено: {path} | {len(df):,} рядків")

    return df


def gold_events(events: pd.DataFrame, campaigns: pd.DataFrame) -> pd.DataFrame:
    logger.info("=== GOLD: events (3NF) ===")
    df = events.copy()

    # замінюємо CampaignName на campaign_id
    name_to_id = campaigns.set_index("campaign_name")["campaign_id"].to_dict()
    df["campaign_id"] = df["CampaignName"].map(name_to_id)
    df = df.drop(columns=["CampaignName"])

    # перейменовуємо колонки
    df.rename(columns={
        "EventID":        "event_id",
        "UserID":         "user_id",
        "Device":         "device",
        "Location":       "location",
        "Timestamp":      "event_timestamp",
        "BidAmount":      "bid_amount",
        "AdCost":         "ad_cost",
        "AdRevenue":      "ad_revenue",
        "ClickTimestamp": "click_timestamp",
    }, inplace=True)

    # впорядковуємо колонки
    df = df[[
        "event_id", "campaign_id", "user_id", "device", "location",
        "event_timestamp", "bid_amount", "ad_cost", "ad_revenue", "click_timestamp"
    ]]

    path = GOLD_DIR / "events.parquet"
    df.to_parquet(path, index=False)
    logger.info(f"Збережено: {path} | {len(df):,} рядків")

    return df