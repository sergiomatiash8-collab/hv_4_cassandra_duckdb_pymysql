from loguru import logger
from pathlib import Path
import sys


Path("logs").mkdir(exist_ok=True)
logger.add("logs/pipeline.log", rotation="10 MB", level="INFO")

from etl.extract.extract import extract
from etl.transform.bronze import bronze_events, bronze_campaigns, bronze_users
from etl.transform.silver import silver_events, silver_campaigns, silver_users
from etl.transform.gold   import gold_advertisers, gold_campaigns, gold_users, gold_events
from etl.load.load        import load_all


def run():
    logger.info("========== PIPELINE СТАРТ ==========")

    
    logger.info("--- КРОК 1: EXTRACT (RAW) ---")
    raw = extract()

    
    logger.info("--- КРОК 2: BRONZE (1NF) ---")
    b_events    = bronze_events(raw["events"])
    b_campaigns = bronze_campaigns(raw["campaigns"])
    b_users     = bronze_users(raw["users"])

   
    logger.info("--- КРОК 3: SILVER (2NF) ---")
    s_events    = silver_events(b_events)
    s_campaigns = silver_campaigns(b_campaigns)
    s_users     = silver_users(b_users)

    
    logger.info("--- КРОК 4: GOLD (3NF) ---")
    g_advertisers = gold_advertisers(s_campaigns)
    g_campaigns   = gold_campaigns(s_campaigns, g_advertisers)
    g_users       = gold_users(s_users)
    g_events      = gold_events(s_events, g_campaigns)

    
    logger.info("--- КРОК 5: LOAD → MySQL ---")
    load_all(g_advertisers, g_campaigns, g_users, g_events)

    logger.info("========== PIPELINE ЗАВЕРШЕНО ==========")


if __name__ == "__main__":
    run()