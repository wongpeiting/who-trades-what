# Executive Disclosures Explorer

A searchable public database of securities transactions, holdings, and income disclosed by senior U.S. executive-branch officials and President Trump, joined to the federal contracts their agencies award.

**34,845 disclosure line items · 35 officials · transactions on/after 2025-01-20 · snapshot July 2026**

---

## Run locally

```bash
pip install flask gunicorn
python app.py
```

Then open <http://localhost:5000> in your browser.

Alternatively:

```bash
pip install -r requirements.txt
flask run
```

The app reads `data/trades.db` (SQLite, read-only). Do not move or rename that file.

---

## Deploy to Render

1. Push this repository to GitHub (make sure `data/trades.db` is committed — Render needs the file at deploy time).
2. On [render.com](https://render.com), click **New → Web Service** and connect your repo.
3. Set:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
4. Click **Deploy**.

> **SQLite note:** Render's free tier uses an ephemeral filesystem. If you need the database to persist across deploys, use Render's **Persistent Disk** (attach it at `/opt/render/project/src/data`) or migrate to a Postgres-backed version. For a read-only snapshot database that ships with the repo, committing `data/trades.db` directly is simplest.

---

## Routes

| Route | Description |
|---|---|
| `GET /` | Search + filter + paginated results table |
| `GET /export` | Stream CSV of all matching rows |
| `GET /download` | Bulk download page + data dictionary |
| `GET /download/full.csv` | Full 34,845-row CSV |
| `GET /official/<id>` | Official profile page |
| `GET /methodology` | Methodology, sources, limits |
| `GET /api/count` | JSON row count for given filters (used by methodology page widget) |

---

## Filter parameters (GET)

`query`, `kind` (transaction/holding), `official`, `agency`, `txn_type`, `flag` (core_contractor / late / tariff_pause / regulates_sector), `amount_min`, `page`.

---

## Data source

OGE Form 278-T and 278e filings (public domain, 17 U.S.C. §105), joined to USASpending.gov contract awards. See [Methodology](/methodology) for full details.
