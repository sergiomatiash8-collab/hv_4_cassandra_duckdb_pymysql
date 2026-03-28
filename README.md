# hv_4_cassandra_duckdb_pymysql

**Base from hv_1** - розширена версія з DuckDB та Cassandra支援

# HW4 — Ad Performance Analytics with Cassandra

ETL pipeline for AdTech data: extracts from MySQL, transforms with DuckDB, loads into Apache Cassandra.

## Stack

| Layer | Tool | Why |
|---|---|---|
| Extract | PyMySQL SSCursor | streaming, no RAM overload |
| Transform | DuckDB | fast SQL aggregations |
| Load | scylla-driver | Python 3.13 compatible Cassandra driver |
| Source DB | MySQL 8.0 | 10M ad events from HW1 |
| Target DB | Apache Cassandra 4.1 | query-first NoSQL |
| GUI | TablePlus | CQL queries and screenshots |

## Project structure
```
etl_mysql/               # HW1 pipeline (CSV → MySQL)
etl_cassandra/
├── extract.py           # reads from MySQL via PyMySQL
├── transform.py         # aggregates via DuckDB
├── load.py              # writes to Cassandra
└── cassandra_pipeline.py
scripts/
├── 01_create_tables.sql
├── 02_cassandra_schema.cql
└── 04_queries.cql
docker-compose.yml       # MySQL + Cassandra
screenshots/
```

## Cassandra schema

5 tables designed per query (query-first modeling):

| Table | Query |
|---|---|
| `campaign_daily_stats` | CTR per campaign per day |
| `advertiser_spend` | top advertisers by total spend |
| `user_ad_history` | last 10 ads per user |
| `user_click_stats` | top 10 users by clicks |
| `advertiser_spend_by_region` | top advertisers by region |

## How to run

**1. Start containers**
```bash
docker-compose up -d
```

**2. Create Cassandra schema**
```bash
docker exec -it adtech_cassandra cqlsh -f /dev/stdin < scripts/02_cassandra_schema.cql
```

**3. Activate virtual environment**
```bash
hv_4\Scripts\activate
```

**4. Run ETL**
```bash
python -m etl_cassandra.cassandra_pipeline
```

## Notes

- `scylla-driver` used instead of `cassandra-driver` — official driver does not support Python 3.13
- `AsyncioConnection` set globally before cluster init — required fix for Windows + Python 3.13
- `user_ad_history` table contains all 10M rows — ETL takes ~40 minutes
- `bucket=1` pattern used in `user_click_stats` to enable sorting by clicks across all users