# SkillPulse

SkillPulse is a local, reproducible MVP for the Big Data Systems final project described in `BDA_Final_Report_DRAFT.md`. It turns Taiwan data/AI job postings into role-level skill demand, AI penetration, and AI salary-premium marts for a training-provider dashboard.

The locked MVP focus role is **Data Engineer**, with the full data/AI cluster retained for context and **Backend Engineer** as the non-AI control group.

## Quick Start

Requires Python 3.9+ (the data contract uses pydantic v2).

```powershell
python -m pip install -r requirements.txt
python -m skillpulse.run_all --sample
python -m streamlit run skillpulse/dashboard/app.py
```

After the third command, open <http://localhost:8501> in a browser.

The sample run is offline: no network, no API key, no Kafka. It writes:

- `output/figures/figure1_ai_penetration.png`
- `output/figures/figure2_ai_premium_vs_backend.png`
- `output/marts/*.csv` and `output/marts/*.parquet`
- `data/lake/*.parquet`

If PySpark is installed, `run_all` uses Spark local mode. If PySpark is missing, it falls back to the same Python/pandas transformation so the demo remains runnable. To install and enforce Spark:

```powershell
python -m pip install -r requirements-spark.txt
python -m skillpulse.run_all --sample --require-spark
```

## Reproduce Data Collection

Fixture collection into the append-only event log:

```powershell
python -m skillpulse.ingestion.collect --sample
python -m skillpulse.run_all --input data/raw/postings_collected.json
```

Best-effort live collection is explicit and rate-limited:

```powershell
python -m skillpulse.ingestion.collect --source 104 --keyword "Data Engineer" --keyword "資料工程師" --limit 20
```

If 104 returns a Cloudflare/browser challenge, use the manual URL fallback:

1. Open 104 in your normal browser.
2. Search for the target role.
3. Copy several job detail URLs into `data/raw/104_urls.txt`, one URL per line.
4. Import those detail pages:

```powershell
python -m skillpulse.ingestion.collect --source 104 --url-file data/raw/104_urls.txt --headed-browser
python -m skillpulse.run_all --input data/raw/postings_collected.json
```

104 browser fallback and Cake collection require Playwright:

```powershell
python -m pip install -r requirements-scraping.txt
python -m playwright install chromium
python -m skillpulse.ingestion.collect --source 104 --keyword "Data Engineer" --limit 20 --headed-browser
python -m skillpulse.ingestion.collect --source cake --keyword "AI Engineer" --limit 20
```

## Tests

```powershell
python -m pytest tests
```

The focused tests cover the extractor and Taiwan salary parser, the two normalization steps that directly feed Figures 1 and 2.

## Local Architecture Mapping

| Report architecture | MVP implementation | Scale-out path |
|---|---|---|
| Kafka topic `raw-postings` | Append-only `data/raw/events.jsonl` | Start the optional Kafka profile and publish each scraper result as an event |
| MongoDB raw store | Local raw JSON arrays and JSONL event log | Replace `events.py` writer with MongoDB insert or dual-write |
| MinIO/S3 data lake | Local Parquet under `data/lake/` | Change the Parquet path to `s3a://...` with MinIO/S3 credentials |
| Spark batch processing | PySpark local mode, with pandas fallback for demo continuity | Run the same job on a Spark cluster/executors |
| PostgreSQL serving store | DuckDB when installed, plus CSV/Parquet marts always | Use Postgres/ClickHouse/BigQuery for concurrent dashboard/API serving |
| Airflow orchestration | `python -m skillpulse.run_all` / `make sample` | Wrap collect/process/publish commands in an Airflow DAG |
| Streamlit dashboard | `skillpulse/dashboard/app.py` | Deploy to Streamlit Cloud/Render/Fly.io |

Optional single-broker Kafka-compatible service:

```powershell
docker compose --profile kafka up -d kafka
```

The default pipeline does not require Kafka.

## Repository Layout

```text
skillpulse/
  schema.py                  # data contract and salary parser
  extraction.py              # taxonomy dictionary matching
  classification.py          # skill-fingerprint role classifier
  processing/pipeline.py     # sample/live raw -> normalized records
  aggregation.py             # serving marts
  analysis/figures.py        # Figures 1 and 2
  ingestion/collect.py       # reproducible collection entry point
  ingestion/sources/         # 104 and Cake adapters
  dashboard/app.py           # read-only Streamlit dashboard
taxonomy/
  skills_v1.yaml
  roles_v1.yaml
data/sample/postings_sample.json
tests/
```

## Current MVP Boundary

Implemented: data contract, fixtures, skill extraction, salary parsing, rule-based role classification, Figures 1 and 2, local marts, Streamlit dashboard, and reproducible fixture collection.

Deferred bonus items: Figure 3 co-occurrence, Figure 4 curriculum gap, FastAPI endpoint, fuller containerized stack, Airflow DAG.
