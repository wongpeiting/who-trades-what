"""
Executive-Branch Disclosures Explorer
Flask + SQLite (read-only) app.
"""

import csv
import io
import os
import sqlite3

from flask import (
    Flask, Response, abort, g, redirect, render_template, request,
    send_from_directory, url_for,
)

app = Flask(__name__)
# Reload templates on change so edits show without a server restart (harmless in prod).
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.auto_reload = True

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "data", "trades.db")
# Directories holding the original source PDFs, served read-only via /source/<file>.
SOURCE_DIRS = [
    os.path.join(BASE_DIR, "data", "raw_pdfs"),
    os.path.join(BASE_DIR, "data", "raw_278e"),
]
PER_PAGE = 50


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ---------------------------------------------------------------------------
# Query builder (shared between / and /export)
# ---------------------------------------------------------------------------

def build_query(query, kind, official, agency, txn_type, flag, amount_min):
    """Return (WHERE clause, params list) — never interpolates user input."""
    conditions = []
    params = []

    # Full-text search across the searchable text columns (incl. income + sector so that
    # disclosed content like the World Liberty crypto income surfaces, not just descriptions)
    if query:
        q = f"%{query}%"
        conditions.append(
            "(official_name LIKE ? OR raw_description LIKE ? OR ticker LIKE ? OR title LIKE ? "
            "OR income_type LIKE ? OR income_amount LIKE ? OR sector LIKE ? OR agency LIKE ?)"
        )
        params.extend([q, q, q, q, q, q, q, q])

    if kind:
        conditions.append("item_kind = ?")
        params.append(kind)

    if official:
        conditions.append("official_name = ?")
        params.append(official)

    if agency:
        conditions.append("agency = ?")
        params.append(agency)

    if txn_type:
        conditions.append("txn_type = ?")
        params.append(txn_type)

    if flag == "core_contractor":
        conditions.append("agency_core_contractor = 1")
    elif flag == "late":
        conditions.append("disclosure_lag_days > 45")
    elif flag == "tariff_pause":
        conditions.append("before_tariff_pause = 1")
    elif flag == "regulates_sector":
        conditions.append("regulates_own_sector = 1")
    elif flag == "near_action":
        conditions.append("near_agency_action = 1")
    elif flag == "crypto":
        # Curated collection: the President's World Liberty / crypto-wallet lines, which are
        # named inconsistently (token sales, coin-named cold wallets, WLF Holdco equity) so no
        # single keyword catches them. Sums to $592,442,316.
        conditions.append(
            "(raw_description LIKE '%Cryptocurrency Wallet%' "
            "OR raw_description LIKE '%Token Sales%' "
            "OR raw_description LIKE '%WLF Holdco%')"
        )

    if amount_min:
        try:
            am = int(amount_min)
            conditions.append("value_min >= ?")
            params.append(am)
        except ValueError:
            pass

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    return where, params


def fetch_dropdown_data(db):
    officials = db.execute(
        "SELECT DISTINCT official_id, official_name FROM disclosure_line_items ORDER BY official_name"
    ).fetchall()
    agencies = [
        r["agency"]
        for r in db.execute(
            "SELECT DISTINCT agency FROM disclosure_line_items WHERE agency IS NOT NULL ORDER BY agency"
        )
    ]
    txn_types = [
        r["txn_type"]
        for r in db.execute(
            "SELECT DISTINCT txn_type FROM disclosure_line_items WHERE txn_type IS NOT NULL ORDER BY txn_type"
        )
    ]
    return officials, agencies, txn_types


def flag_badges(row):
    badges = []
    if row["agency_core_contractor"]:
        badges.append(("contractor", "agency contractor"))
    if row["disclosure_lag_days"] and row["disclosure_lag_days"] > 45:
        badges.append(("late", f"late {row['disclosure_lag_days'] - 45}d"))
    if row["before_tariff_pause"]:
        badges.append(("tariff", "pre-tariff-pause"))
    try:
        if row["near_agency_action"]:
            badges.append(("action", "near agency action"))
    except IndexError:
        pass
    return badges


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    db = get_db()
    query = request.args.get("query", "").strip()
    kind = request.args.get("kind", "").strip()
    official = request.args.get("official", "").strip()
    agency = request.args.get("agency", "").strip()
    txn_type = request.args.get("txn_type", "").strip()
    flag = request.args.get("flag", "").strip()
    amount_min = request.args.get("amount_min", "").strip()
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1

    where, params = build_query(query, kind, official, agency, txn_type, flag, amount_min)

    total = db.execute(
        f"SELECT COUNT(*) FROM disclosure_line_items {where}", params
    ).fetchone()[0]

    offset = (page - 1) * PER_PAGE
    rows = db.execute(
        f"""
        SELECT item_id, official_id, official_name, title, item_kind,
               raw_description, ticker, txn_type, txn_date, value_bracket,
               owner, income_type, income_amount,
               agency_core_contractor, disclosure_lag_days, before_tariff_pause,
               regulates_own_sector, near_agency_action, source_url, source_file
        FROM disclosure_line_items
        {where}
        ORDER BY txn_date DESC, item_id
        LIMIT ? OFFSET ?
        """,
        params + [PER_PAGE, offset],
    ).fetchall()

    officials_list, agencies_list, txn_types_list = fetch_dropdown_data(db)

    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    showing_from = offset + 1 if total else 0
    showing_to = min(offset + PER_PAGE, total)

    rows_with_flags = [(row, flag_badges(row)) for row in rows]

    # official_id -> portrait, for the face beside each name in the results
    photos = {r["official_id"]: r["photo_url"] for r in db.execute(
        "SELECT official_id, photo_url FROM officials WHERE photo_url IS NOT NULL AND photo_url<>''")}

    # Landing overview stats — only on the empty (no-search) home state.
    stats = None
    if not (query or kind or official or agency or txn_type or flag or amount_min):
        s = db.execute(
            """SELECT
                 (SELECT COUNT(*) FROM disclosure_line_items) lines,
                 (SELECT COUNT(*) FROM disclosure_line_items WHERE item_kind='transaction') txns,
                 (SELECT COUNT(*) FROM disclosure_line_items WHERE item_kind='holding') holdings,
                 (SELECT COUNT(*) FROM disclosure_line_items WHERE disclosure_lag_days>45) late,
                 (SELECT COUNT(*) FROM disclosure_line_items WHERE agency_core_contractor=1) core"""
        ).fetchone()
        stats = dict(s)

    return render_template(
        "index.html",
        rows=rows_with_flags,
        photos=photos,
        stats=stats,
        query=query,
        kind=kind,
        official=official,
        agency=agency,
        txn_type=txn_type,
        flag=flag,
        amount_min=amount_min,
        page=page,
        total=total,
        total_pages=total_pages,
        showing_from=showing_from,
        showing_to=showing_to,
        officials_list=officials_list,
        agencies_list=agencies_list,
        txn_types_list=txn_types_list,
    )


@app.route("/export")
def export():
    db = get_db()
    query = request.args.get("query", "").strip()
    kind = request.args.get("kind", "").strip()
    official = request.args.get("official", "").strip()
    agency = request.args.get("agency", "").strip()
    txn_type = request.args.get("txn_type", "").strip()
    flag = request.args.get("flag", "").strip()
    amount_min = request.args.get("amount_min", "").strip()

    where, params = build_query(query, kind, official, agency, txn_type, flag, amount_min)

    rows = db.execute(
        f"""
        SELECT item_id, official_id, official_name, title, party, agency,
               source_file, form_type, part, item_kind, owner, raw_description,
               ticker, sector, txn_type, txn_date, value_min, value_max,
               value_bracket, income_type, income_amount, eif, is_preconfirmation,
               disclosure_lag_days, before_tariff_pause, agency_pays_company,
               agency_core_contractor, regulates_own_sector, near_agency_action, source_url
        FROM disclosure_line_items
        {where}
        ORDER BY txn_date DESC, item_id
        """,
        params,
    ).fetchall()

    def generate():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "item_id", "official_id", "official_name", "title", "party", "agency",
            "source_file", "form_type", "part", "item_kind", "owner", "raw_description",
            "ticker", "sector", "txn_type", "txn_date", "value_min", "value_max",
            "value_bracket", "income_type", "income_amount", "eif", "is_preconfirmation",
            "disclosure_lag_days", "before_tariff_pause", "agency_pays_company",
            "agency_core_contractor", "regulates_own_sector", "near_agency_action", "source_url",
        ])
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate()
        for row in rows:
            writer.writerow(list(row))
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate()

    return Response(
        generate(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=executive_disclosures_export.csv"
        },
    )


@app.route("/download")
def download():
    return render_template("download.html")


@app.route("/download/full.csv")
def download_full():
    db = get_db()
    rows = db.execute(
        """
        SELECT item_id, official_id, official_name, title, party, agency,
               source_file, form_type, part, item_kind, owner, raw_description,
               ticker, sector, txn_type, txn_date, value_min, value_max,
               value_bracket, income_type, income_amount, eif, is_preconfirmation,
               disclosure_lag_days, before_tariff_pause, agency_pays_company,
               agency_core_contractor, regulates_own_sector, near_agency_action, source_url
        FROM disclosure_line_items
        ORDER BY official_name, txn_date, item_id
        """
    ).fetchall()

    def generate():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "item_id", "official_id", "official_name", "title", "party", "agency",
            "source_file", "form_type", "part", "item_kind", "owner", "raw_description",
            "ticker", "sector", "txn_type", "txn_date", "value_min", "value_max",
            "value_bracket", "income_type", "income_amount", "eif", "is_preconfirmation",
            "disclosure_lag_days", "before_tariff_pause", "agency_pays_company",
            "agency_core_contractor", "regulates_own_sector", "near_agency_action", "source_url",
        ])
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate()
        for row in rows:
            writer.writerow(list(row))
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate()

    return Response(
        generate(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=disclosure_line_items_full.csv"
        },
    )


@app.route("/official/<int:official_id>")
def official_profile(official_id):
    db = get_db()
    official_row = db.execute(
        "SELECT * FROM officials WHERE official_id = ?", (official_id,)
    ).fetchone()
    if not official_row:
        return "Official not found", 404

    name = official_row["full_name"]

    txn_count = db.execute(
        "SELECT COUNT(*) FROM disclosure_line_items WHERE official_id = ? AND item_kind='transaction'",
        (official_id,),
    ).fetchone()[0]

    holding_count = db.execute(
        "SELECT COUNT(*) FROM disclosure_line_items WHERE official_id = ? AND item_kind='holding'",
        (official_id,),
    ).fetchone()[0]

    late_count = db.execute(
        "SELECT COUNT(*) FROM disclosure_line_items WHERE official_id = ? AND disclosure_lag_days > 45",
        (official_id,),
    ).fetchone()[0]

    contractor_count = db.execute(
        "SELECT COUNT(*) FROM disclosure_line_items WHERE official_id = ? AND agency_core_contractor=1",
        (official_id,),
    ).fetchone()[0]

    # In-profile search + pagination (this official's rows can number tens of thousands)
    q = request.args.get("q", "").strip()
    kind = request.args.get("kind", "").strip()
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1

    where = "WHERE official_id = ?"
    params = [official_id]
    if q:
        where += (" AND (raw_description LIKE ? OR ticker LIKE ? OR txn_type LIKE ?"
                  " OR income_type LIKE ? OR income_amount LIKE ? OR value_bracket LIKE ?)")
        like = f"%{q}%"
        params += [like] * 6
    if kind in ("transaction", "holding"):
        where += " AND item_kind = ?"
        params.append(kind)

    total = db.execute(
        f"SELECT COUNT(*) FROM disclosure_line_items {where}", params
    ).fetchone()[0]
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    offset = (page - 1) * PER_PAGE

    items = db.execute(
        f"""
        SELECT item_id, item_kind, raw_description, ticker, txn_type, txn_date,
               value_bracket, income_type, income_amount, owner,
               agency_core_contractor, disclosure_lag_days, before_tariff_pause,
               regulates_own_sector, near_agency_action, source_url, source_file
        FROM disclosure_line_items
        {where}
        ORDER BY txn_date DESC, item_id
        LIMIT ? OFFSET ?
        """,
        params + [PER_PAGE, offset],
    ).fetchall()

    items_with_flags = [(row, flag_badges(row)) for row in items]

    return render_template(
        "official.html",
        official=official_row,
        txn_count=txn_count,
        holding_count=holding_count,
        late_count=late_count,
        contractor_count=contractor_count,
        items=items_with_flags,
        q=q, kind=kind, page=page, total=total, total_pages=total_pages,
        showing_from=(offset + 1 if total else 0), showing_to=min(offset + PER_PAGE, total),
    )


@app.route("/methodology")
def methodology():
    def read_file(path):
        try:
            with open(path, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return None

    base = os.path.dirname(__file__)
    completeness_md = read_file(os.path.join(base, "COMPLETENESS.md"))
    sources_md = read_file(os.path.join(base, "Subject-and-Sources.md"))

    return render_template(
        "methodology.html",
        completeness_md=completeness_md,
        sources_md=sources_md,
    )


@app.route("/api/count")
def api_count():
    db = get_db()
    query = request.args.get("query", "").strip()
    kind = request.args.get("kind", "").strip()
    official = request.args.get("official", "").strip()
    agency = request.args.get("agency", "").strip()
    txn_type = request.args.get("txn_type", "").strip()
    flag = request.args.get("flag", "").strip()
    amount_min = request.args.get("amount_min", "").strip()

    where, params = build_query(query, kind, official, agency, txn_type, flag, amount_min)
    count = db.execute(
        f"SELECT COUNT(*) FROM disclosure_line_items {where}", params
    ).fetchone()[0]

    from flask import jsonify
    return jsonify({"count": count})


@app.route("/network")
def network():
    return redirect("/conflicts#network")


_TICKER_NAMES = None


def ticker_name(tk):
    """Real company name for a ticker (SEC EDGAR title), falling back to the ticker itself."""
    global _TICKER_NAMES
    if _TICKER_NAMES is None:
        import json
        _TICKER_NAMES = {}
        try:
            for e in json.load(open(os.path.join(BASE_DIR, "data/interim/sec_tickers.json"))).values():
                t = (e.get("ticker") or "").upper()
                if t and t not in _TICKER_NAMES:
                    _TICKER_NAMES[t] = e.get("title") or t
        except Exception:
            _TICKER_NAMES = {}
    return _TICKER_NAMES.get((tk or "").upper(), tk)


@app.route("/api/network")
def api_network():
    """Nodes + edges for the conflict network: official → agency → company → (traded by) official."""
    db = get_db()
    rows = db.execute("""
        SELECT DISTINCT d.official_id, d.official_name, d.agency, d.ticker,
               (SELECT SUM(c.award_amount) FROM contract_awards c
                 WHERE c.recipient_ticker=d.ticker AND c.awarding_agency=d.agency) AS award,
               d.agency_core_contractor
        FROM disclosure_line_items d
        WHERE d.agency_pays_company=1 AND d.ticker IS NOT NULL AND d.ticker<>''
    """).fetchall()
    nodes, edges, seen = {}, [], set()

    def add(nid, label, group, title=None):
        if nid not in nodes:
            nodes[nid] = {"id": nid, "label": label, "group": group, "title": title or label}

    def money(v):
        if not v: return ""
        v = float(v)
        return f"${v/1e9:.1f}B" if v >= 1e9 else (f"${v/1e6:.0f}M" if v >= 1e6 else f"${v:,.0f}")

    for r in rows:
        off = f"off:{r['official_id']}"; ag = f"ag:{r['agency']}"; co = f"co:{r['ticker']}"
        short = (r["official_name"] or "").split(",")[0]
        add(off, short, "official", r["official_name"])
        add(ag, r["agency"], "agency")
        cname = ticker_name(r["ticker"])
        add(co, cname, "company", f"{cname} ({r['ticker']}) — agency pays {money(r['award'])}")
        for e in ((off, ag, "heads"), (off, co, "traded")):
            k = (e[0], e[1])
            if k not in seen:
                seen.add(k); edges.append({"from": e[0], "to": e[1], "label": e[2]})
        k = (ag, co)
        if k not in seen:
            seen.add(k)
            edges.append({"from": ag, "to": co, "label": money(r["award"]),
                          "color": {"color": "#c0392b"} if r["agency_core_contractor"] else {"color": "#bbb"},
                          "width": 3 if r["agency_core_contractor"] else 1})
    from flask import jsonify
    return jsonify({"nodes": list(nodes.values()), "edges": edges})


@app.route("/conflicts")
def conflicts():
    """The trades in companies the official's own agency pays under federal contract."""
    db = get_db()
    rows = db.execute("""
        SELECT d.official_id, d.official_name, d.agency, d.ticker, d.raw_description,
               d.item_kind, d.txn_type, d.txn_date, d.value_bracket,
               d.agency_core_contractor, d.source_url, d.source_file,
               (SELECT SUM(c.award_amount) FROM contract_awards c
                 WHERE c.recipient_ticker = d.ticker AND c.awarding_agency = d.agency) AS award_total
        FROM disclosure_line_items d
        WHERE d.agency_pays_company = 1
        ORDER BY d.agency_core_contractor DESC,
                 award_total DESC NULLS LAST, d.official_name, d.txn_date
    """).fetchall()
    n_core = sum(1 for r in rows if r["agency_core_contractor"] == 1)

    # ── Section 2: traded near a dated action by the official's own agency ──
    tl_ready = db.execute("SELECT 1 FROM pragma_table_info('transactions') WHERE name='near_agency_action'").fetchone()
    tl_by_official = tl_leads = []
    tl_total = 0
    if tl_ready:
        tl_by_official = db.execute(
            """SELECT o.full_name, o.official_id, o.agency, COUNT(*) n
               FROM transactions t JOIN filings f ON t.filing_id=f.filing_id
               JOIN officials o ON f.official_id=o.official_id
               WHERE t.near_agency_action=1
               GROUP BY o.official_id ORDER BY (o.is_president) ASC, n DESC""").fetchall()
        tl_total = db.execute("SELECT COUNT(*) FROM transactions WHERE near_agency_action=1").fetchone()[0]
        tl_leads = db.execute(
            """SELECT o.full_name, o.official_id, o.agency, t.ticker, t.txn_type, t.txn_date,
                      t.raw_description, t.nearest_action_date, t.nearest_action_title,
                      t.nearest_action_url, f.source_pdf_url
               FROM transactions t JOIN filings f ON t.filing_id=f.filing_id
               JOIN officials o ON f.official_id=o.official_id
               WHERE t.near_agency_action=1 AND o.is_president=0 AND t.ticker IS NOT NULL AND t.ticker<>''
               ORDER BY t.txn_date LIMIT 60""").fetchall()

    return render_template("conflicts.html", rows=rows, n_total=len(rows), n_core=n_core,
                           tl_by_official=tl_by_official, tl_total=tl_total, tl_leads=tl_leads)


@app.route("/timeline")
def timeline_redirect():
    return redirect("/conflicts#actions")


@app.route("/leaderboards")
def leaderboards():
    """Who trades most, holds most, and files latest — President shown separately."""
    db = get_db()

    def board(metric, where):
        rows = db.execute(f"""
            SELECT o.official_id, o.full_name, o.agency, o.is_president, o.photo_url, {metric} v
            FROM disclosure_line_items d JOIN officials o ON o.official_id = d.official_id
            {where} GROUP BY o.official_id HAVING v > 0 ORDER BY v DESC""").fetchall()
        pres = next((r for r in rows if r["is_president"]), None)
        cab = [r for r in rows if not r["is_president"]][:10]
        cabmax = max((r["v"] for r in cab), default=1)
        return {"president": pres, "cabinet": cab, "cabmax": cabmax}

    # Fair comparison: rank the transaction boards on the COMMON basis every official
    # shares — the periodic 278-T report. Trump is the only one with a filed annual, so
    # his annual transactions are shown separately as context, not mixed into the ranking.
    trump_annual = db.execute(
        """SELECT COUNT(*) FROM disclosure_line_items
           WHERE official_id=(SELECT official_id FROM officials WHERE is_president=1)
             AND item_kind='transaction' AND form_type LIKE '278e%'""").fetchone()[0]
    cov = db.execute(
        """SELECT MIN(txn_date) mn, MAX(txn_date) mx FROM disclosure_line_items
           WHERE item_kind='transaction' AND txn_date>='2025-01-20'""").fetchone()

    def friendly(iso):
        from datetime import date
        try:
            return date.fromisoformat(iso).strftime("%-d %b %Y")
        except Exception:
            return iso or "?"
    coverage = {"min": friendly(cov["mn"]), "max": friendly(cov["mx"]), "snapshot": "5 July 2026"}
    return render_template(
        "leaderboards.html",
        active=board("COUNT(*)", "WHERE d.item_kind='transaction' AND d.form_type='278-T'"),
        holdings=board("SUM(COALESCE(d.value_max,0))", "WHERE d.item_kind='holding'"),
        late=board("COUNT(*)", "WHERE d.disclosure_lag_days > 45"),
        trump_annual=trump_annual, coverage=coverage,
    )




@app.route("/timing")
def timing():
    """Did these trades beat the market? Forward returns vs SPY, direction-aware."""
    db = get_db()
    has_table = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='txn_returns'").fetchone()
    if not has_table:
        return render_template("timing.html", ready=False)
    overall = db.execute(
        """SELECT COUNT(*) n,
                  AVG(timed_5)  mean5,  AVG(CASE WHEN timed_5  IS NULL THEN NULL WHEN timed_5 >0 THEN 1.0 ELSE 0 END) beat5,
                  AVG(timed_30) mean30, AVG(CASE WHEN timed_30 IS NULL THEN NULL WHEN timed_30>0 THEN 1.0 ELSE 0 END) beat30,
                  AVG(timed_90) mean90, AVG(CASE WHEN timed_90 IS NULL THEN NULL WHEN timed_90>0 THEN 1.0 ELSE 0 END) beat90
           FROM txn_returns WHERE timed_5 IS NOT NULL""").fetchone()
    leaders = db.execute(
        """SELECT r.official, o.official_id, COUNT(*) n, AVG(r.timed_90) mean90,
                  AVG(CASE WHEN r.timed_90>0 THEN 1.0 ELSE 0 END) beat90
           FROM txn_returns r LEFT JOIN officials o ON o.full_name = r.official
           WHERE r.timed_90 IS NOT NULL
           GROUP BY r.official HAVING n >= 20 ORDER BY mean90 DESC""").fetchall()
    top = db.execute(
        """SELECT r.official, r.ticker, r.txn_date, r.txn_type, r.timed_90,
                  t.amount_bracket AS value_bracket, t.raw_description, f.source_pdf_url
           FROM txn_returns r JOIN transactions t ON r.txn_id = t.txn_id
           JOIN filings f ON t.filing_id = f.filing_id
           WHERE r.timed_90 IS NOT NULL
           ORDER BY r.timed_90 DESC LIMIT 20""").fetchall()
    return render_template("timing.html", ready=True, overall=overall, leaders=leaders, top=top)


@app.route("/source/<path:filename>")
def source_pdf(filename):
    """Serve an original disclosure PDF by its basename, read-only.

    Rows whose source is a local file (Trump's annual 278e and the vision-transcribed
    2026 278-Ts, plus locally-held Cabinet filings) link here; rows with a public OGE
    URL link straight to OGE. send_from_directory guards against path traversal.
    """
    base = os.path.basename(filename)  # ignore any path components in the request
    for directory in SOURCE_DIRS:
        if os.path.isfile(os.path.join(directory, base)):
            return send_from_directory(directory, base, mimetype="application/pdf")
    abort(404)


if __name__ == "__main__":
    # macOS reserves port 5000 for AirPlay; use 5001 locally.
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, port=port)
