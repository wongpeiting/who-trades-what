# Document Completeness Audit
**Date:** 2026-07-04  
**Scope:** 34 current-administration officials — periodic 278-T transaction filings + 278e holdings disclosures  
**Sources checked:** `pas_index_expanded.html` + `pas_index_expanded_p2.html` (OGE PAS index cache), `filings_manifest.csv`, `raw_pdfs/`, `raw_278e/`, `trades.db` (filings + transactions + holdings tables), `download_278e_log.csv`, `extract_progress.log`

---

## Coverage Matrix

Columns: **H-278T** = 278-T count in OGE HTML index | **M-278T** = in manifest | **D-278T** = in DB | **H-278e** = nominee/annual 278e in HTML | **D-278e** = downloaded to `raw_278e/` | **Holdings** = rows in holdings table

| Official | H-278T | M-278T | D-278T | H-278e | D-278e | Holdings | Status |
|---|---|---|---|---|---|---|---|
| Bailey, Sara | 1 | 1 | 1 | 1 | 1 | 26 | OK |
| Bedford, Bryan | 4 | 4 | **3** | 1 | 1 | 226 | **GAP: 11.03 extracted 0 rows** |
| Bessent, Scott | 2 | 2 | 2 | 1 | 1 | 50 | OK |
| Bisignano, Frank J | 5 | 5 | 5 | 1 | 1 | 87 | OK |
| Blanche, Todd | 1 | 1 | 1 | 2* | 2 | 44 | OK (*duplicate in HTML) |
| Bondi, Pam | 1 | 1 | 1 | 1 | 1 | 27 | OK |
| Burgum, Douglas J | 5 | 5 | 5 | 1 | 1 | 248 | OK |
| Chavez-DeRemer, Lori | 1 | 1 | 1 | 1 | 1 | 32 | OK |
| Dixon, Stacey | 5 | 4 | 1 | 4 | 4 | 110 | Note: 2021 filings pre-admin; only exit filing in DB |
| Duffy, Sean | 1 | 1 | 1 | 1 | 1 | 141 | OK |
| Edgar, Troy D | 1 | 1 | 1 | 1 | 1 | 102 | OK |
| Faulkender, Michael W | 2 | 1 | 1 | 1 | 1 | 29 | Note: termination annual in HTML only |
| Gabbard, Tulsi | 1 | 1 | 1 | 1 | 1 | 53 | OK |
| Hegseth, Pete | 1 | 1 | 1 | 1 | 1 | 97 | OK |
| Isaacman, Jared | 2 | 2 | 2 | 2* | 2 | 240 | OK (*duplicate in HTML) |
| Kennedy, Robert F | 1 | 1 | 1 | 1 | **0** | **0** | **GAP: 278e download FAILED** |
| Kratsios, Michael J | 10 | 10 | 10 | 1 | 1 | 47 | OK |
| Kupor, Scott A | 8 | 8 | 8 | 1 | 1 | 1303 | OK |
| Landau, Christopher | 1 | 1 | 1 | 1 | 1 | 226 | OK |
| Lawrence, Paul R | 1 | 1 | 1 | 1 | 1 | 92 | OK |
| Lutnick, Howard | 2 | 2 | 2 | 1 | 1 | 111 | OK |
| MacGregor, Katharine | 4 | 3 | 1 | 1 | 1 | 38 | Note: 2020 filings pre-admin; 2021 TERM in HTML only |
| McMahon, Linda E | 2 | 2 | 2 | 1 | 1 | 278 | OK |
| McMaster, Sean | 5 | 5 | 5 | 1 | 1 | 36 | OK |
| Miran, Stephen I | 3 | 3 | 3 | 2 | 2 | 440 | OK (both original + amended 278e) |
| Mody, Arjun | 1 | 1 | 1 | 1 | 1 | 242 | OK |
| Noem, Kristi | 1 | 1 | 1 | 1 | 1 | 60 | OK |
| Phelan, John | 13 | 13 | 13 | 1 | 1 | 233 | OK |
| Sonderling, Keith | 1 | 1 | 1 | 2 | 2 | 75 | OK (nominee + 2026 annual) |
| Trump, Donald J. | N/A | 17 | **0** | N/A | 1 | **0 (in holdings)** | **SPECIAL — see below** |
| Turner, Eric Scott | 2 | 2 | 2 | 1 | 1 | 50 | OK |
| Vaden, Stephen A | 1 | 1 | 1 | 1 | 1 | 122 | OK |
| Wright, Christopher A | 4 | 4 | 4 | 1 | 1 | 152 | OK |
| Zeldin, Lee | 2 | 2 | **1** | 2 | 2 | 71 | **GAP: 09-24-2025 not downloaded** |

**Summary:**
- **278-T fully covered** (H = M = D, all current-admin filings in DB): **30 of 33 non-Trump officials**
- **278e fully covered** (nominee/annual downloaded + holdings loaded): **32 of 33 non-Trump officials**
- **Trump**: handled separately (not in PAS index; 16/17 periodic 278-T downloaded but not extracted to DB; annual 278e loaded as 21,198 entries in *transactions* table, not holdings)

---

## Prioritized Gap List

### PRIORITY 1 — Missing data that directly affects the analysis

**Gap 1 — Kennedy, Robert F: 278e nominee download FAILED**
- File: `Kennedy, Jr., Robert F.  AMENDED final278.pdf`
- Why missing: HTTP download failed at collection time (per `download_278e_log.csv`, status=`failed`). The URL is valid (exists in HTML index). File not in `raw_278e/`.
- Impact: Kennedy has **0 rows in the holdings table**. His pre-confirmation financial holdings are completely absent from the dataset.
- Fix: Re-download from `https://extapps2.oge.gov/201/Presiden.nsf/PAS+Index/[HEXID]/$FILE/Kennedy, Jr., Robert F.  AMENDED final278.pdf` and rerun holdings extraction.

---

**Gap 2 — Zeldin, Lee: 09-24-2025 278-T not downloaded**
- File: `Lee-Zeldin-09-24-2025-278T.pdf`
- URL: `https://extapps2.oge.gov/201/Presiden.nsf/PAS+Index/1F2CA5D27DDE1D9085258D460031984D/$FILE/Lee-Zeldin-09-24-2025-278T.pdf`
- Why missing: Filing date is **blank** in the manifest (`filing_date` column is empty). The date-based download filter excluded it. The file was never fetched to `raw_pdfs/`.
- Impact: Only 1 of Zeldin's 2 278-T filings (the 06-17-2025 one with 3 transactions) is in the DB. His September 2025 transactions are entirely absent.
- Fix: Download directly via the URL above; add to manifest with date `09.24.2025`; re-run extraction and load step.

---

**Gap 3 — Trump, Donald J.: 9.3.25 278-T blank-date, never downloaded**
- File: `Donald J. Trump 9.3.25 278-T.pdf` (in manifest; 17th entry)
- Why missing: Filing date is blank in manifest. The date filter excluded it. File is NOT in `raw_pdfs/` (only 16 Trump periodic PDFs are present; all others were downloaded manually).
- Impact: The September 3, 2025 filing is missing. This represents trades in the Aug-Sep 2025 period.
- Fix: Source via the OGE Filers view (Trump files outside PAS index). The download URL must be located manually.

---

**Gap 4 — Trump, Donald J.: periodic 278-T extracted 0 rows (scanned PDFs), and 2026 trades not in DB**
- Files affected (0-row extraction per `extract_progress.log`):
  - `Donald J. Trump 10.17.2025 278-T.pdf` (4 pages, 860 KB — scanned)
  - `Donald J. Trump 11.14.2025 278-T.pdf` (3 pages, 844 KB — scanned)
  - `Donald J. Trump 2.26.2026 278-T (1).pdf` (8 pages, 2.5 MB — scanned)
  - `Donald J. Trump 2.26.2026 278-T (2).pdf` (5 pages, 2.0 MB — scanned)
  - `Donald-J-Trump-08.12.2025-278T(2) AMENDED.pdf` (10 pages — scanned)
  - `Donald-J-Trump-08.12.2025-278T(3).pdf` (4 pages — scanned)
  - `Trump, Donald J.-05.08.2026-278T.pdf` (5 pages — scanned)
- The annual 278e (filed 2026-06-29, covering Jan 1–Dec 31 2025) was successfully loaded as 21,198 entries in the **transactions** table — these are annual holdings/position data, not real-time trades.
- **Critical gap**: Trump's 2026 periodic trades (4.20.2026, 5.08.2026, 6.25.2026) are NOT covered by the annual 278e (which stops at Dec 31, 2025). The 4.20.2026 filing extracted 4 rows, 5.08.2026(2) extracted 63 rows, 6.25.2026 extracted 164–239 rows — these exist in `extract_progress.log` but were NOT loaded into the DB transactions table.
- Note: Trump's holdings from the annual 278e are stored as 21,198 rows in the **transactions** table, not in the holdings table (0 rows in holdings for Trump). This is a structural inconsistency.
- Fix (for 2026 trades): Run OCR on the scanned 2026 periodic 278-T PDFs; load the already-extracted rows (from 4.20, 5.08, 6.25 filings) into the DB. For 2025 scanned filings, the annual 278e provides coverage.

---

### PRIORITY 2 — Downloaded but not in DB

**Gap 5 — Bedford, Bryan: 11.03.2025 278-T extracted 0 rows**
- File: `Bryan-Bedford-11.03.2025-278T.pdf` — **present** in `raw_pdfs/` (9,240 bytes, 3 pages)
- Why missing from DB: Extraction yielded 0 rows (per `extract_progress.log`). At 9.2 KB for a 3-page filing, this is likely a scanned or otherwise unreadable PDF (possibly a cover page / signature page only, or the OGE server returned an error page at download time).
- Impact: Bedford's November 3, 2025 transactions are absent from the dataset. He has 3 of 4 filings in the DB.
- Fix: Inspect the PDF manually. If it is a cover-page stub, the missing transactions may be contained in an adjacent filing. If readable, re-run extraction on this file alone and reload.

---

### PRIORITY 3 — Pre-admin / termination filings (not critical for current-admin analysis)

**Gap 6 — Dixon, Stacey: 3 Biden-era 278-T not downloaded**
- Files: `Stacy-Dixon-08.12.2021-278T.pdf`, `Stacey-Dixon-08.24.2021-278T.pdf`, `Stacey-Dixon-08.24.2021-278T(1).pdf`
- In manifest (dates Aug 2021) but not in `raw_pdfs/`. These predate the current administration (Jan 2025) by over 3 years.
- Current-admin relevance: Low. Dixon's exit 278-T (02.10.2025) IS in the DB with 3 transactions. Her confidence level in `official_agency.csv` is "unknown", suggesting she may be a former (Biden-era) official. Her pre-confirmation annual 278e for 2022–2024 was downloaded and is in holdings.
- Fix: Skip unless Dixon is confirmed as a current-admin position-holder.

**Gap 7 — Dixon, Stacey: `Stacey-Dixon-2025-278TERM.pdf` in HTML only**
- A termination annual report exists in the PAS index HTML but is NOT in the manifest and not downloaded. This would document her financial position at departure.
- Fix: Download to `raw_278e/` if Dixon is confirmed as current-admin; otherwise low priority.

**Gap 8 — Faulkender, Michael W: `Michael-W-Faulkender-2025-278TERM.pdf` in HTML only**
- A termination annual report is in the HTML index but not in the manifest and not downloaded. Faulkender's 06.26.2025 278-T IS in the DB (1 transaction).
- Fix: Download if annual holdings at departure are needed for analysis.

**Gap 9 — MacGregor, Katharine: 2020 278-T filings in manifest but not downloaded**
- Files: `Katharine-MacGregor-07.01.2020-278T.pdf`, `Katharine-MacGregor-08.13.2020-278T.pdf`
- Trump-1 era filings (2020), not relevant for current admin analysis. Only the 08.07.2025 filing is captured in DB (20 transactions).

**Gap 10 — MacGregor, Katharine: `Katharine-MacGregor-2021-278TERM.pdf` in HTML only**
- Her Trump-1 era termination annual is in HTML but not in the manifest or downloaded. Irrelevant for current-admin purposes; her 2025 re-appointment nominee 278e IS in `raw_278e/`.

---

## Special Notes

### Amended Filings
- **Bessent, Scott**: The AMENDED nominee 278e (`Bessent, Scott  AMENDED final278.pdf`) was captured. This is the operative version.
- **McMaster, Sean**: The AMENDED nominee 278e was captured.
- **Miran, Stephen I**: Both the original and AMENDED nominee 278e were downloaded and are in holdings (440 rows total).
- **Trump (08.12.2025 AMENDED)**: The amended periodic 278-T and a third version were downloaded but extracted 0 rows (scanned). The original 08.12.2025 filing extracted 3 rows.

### Rubio, Marco — Extra file
- `Marco-Rubio-2026-278ANNU.pdf` is in `raw_278e/` and 15 holdings rows for "Rubio, Marco" are in the holdings table. However, **Rubio is not one of the 34 current officials** in `official_agency.csv`. This is a data artifact from a broader collection pass that included the Secretary of State.

### Trump Annual 278e — Structural Note
- Trump's 2026 annual 278e (covering Jan–Dec 2025) was loaded as 21,198 rows in the **transactions** table (not the holdings table). The `form_type` = `278e-Annual`, `txn_date` range = 2025-01-21 to 2025-12-31. These appear as "purchase"/"sale" entries with `txn_date` values that correspond to reporting batches, not actual trade dates. This is a structural inconsistency: other officials' annual 278e data is in the `holdings` table, but Trump's is in `transactions`.

---

## Bottom Line

### Are 278-T filings "complete" for the current cohort?

**Non-Trump officials (33)**: 30 of 33 are fully covered for the current-administration period. Three have gaps:
- Zeldin (1 filing, Sep 2025 — not downloaded; easy to fix via URL)
- Bedford (1 filing, Nov 2025 — downloaded but 0-row extraction; may be a scanned stub)
- Dixon (marginal: pre-admin 2021 filings missing; exit filing is present)

**Trump**: The annual 278e covers all of 2025 (21,198 entries in transactions table). His **2026 periodic trades are not in the DB** — the 4.20, 5.08, and 6.25.2026 filings were downloaded and partially extracted but not loaded. The 9.3.25 filing was never downloaded. The 2026 gap is material if the analysis period extends past December 2025.

### Are 278e filings "complete" for the current cohort?

**Non-Trump officials (33)**: 32 of 33 have nominee 278e downloaded and holdings loaded. The one gap is:
- Kennedy, Robert F — download FAILED; 0 holdings in DB. Must be re-fetched.

**Trump**: Annual 278e downloaded (`Donald-J-Trump-2026-278ANNUAL.pdf`). Holdings loaded as 21,198 rows in `transactions` table (not `holdings` table — structural issue).

### What would close the gaps

| Action | Priority | Officials |
|---|---|---|
| Re-download Kennedy 278e and run holdings extraction | High | Kennedy, Robert F |
| Download Zeldin 09-24-2025 278-T and extract | High | Zeldin, Lee |
| Download Trump 9.3.25 278-T and extract | High | Trump, Donald J. |
| Load Trump 2026 periodic 278-T rows (4.20, 5.08, 6.25) into DB | High | Trump, Donald J. |
| Inspect Bedford 11.03.2025 PDF; OCR/re-extract if scanned | Medium | Bedford, Bryan |
| Download Dixon + MacGregor + Faulkender termination annuals | Low | Dixon, Faulkender, MacGregor |
| Resolve Trump holdings vs transactions structural inconsistency | Medium | Trump, Donald J. |
