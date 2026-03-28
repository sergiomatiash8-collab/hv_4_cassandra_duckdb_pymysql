from pathlib import Path
import pandas as pd
from loguru import logger

RAW_DIR = Path("data/raw")

FILES = {
    "events":    RAW_DIR / "(USE THIS)ad_events_header_updated.csv",
    "campaigns": RAW_DIR / "campaigns.csv",
    "users":     RAW_DIR / "users.csv",
}

def extract() -> dict:
    logger.info("=== RAW шар: читаємо файли як є ===")
    
    dataframes = {}
    
    for name, path in FILES.items():
        logger.info(f"Читаємо {path.name}...")
        df = pd.read_csv(path, dtype=str)
        dataframes[name] = df
        logger.info(f"{name}: {len(df):,} рядків, {len(df.columns)} колонок")
    
    return dataframes