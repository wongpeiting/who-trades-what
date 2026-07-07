# Who Trades What

**A searchable database of the stocks, funds, and income that President Trump and his senior appointees disclose — cross-referenced against the federal contracts and agency actions their own departments control.**

This is built on Flask with SQLite, and deploys on [Render]: [who-trades-what.onrender.com](https://who-trades-what.onrender.com/)

---

## What it is

Senior executive-branch officials must report what they own, earn, and trade under the Ethics in Government Act of 1978. This project collects those filings and turns them into one searchable, cross-referenced dataset so anyone can ask: *do these officials trade in the industries they regulate, in companies their agencies pay under contract, and do they report it on time?*

## What you can explore

- **Search** every disclosed trade, holding, and income line by official, security, ticker, or keyword
- **Potential conflicts** — trades in companies the official's own agency pays under contract, trades near a dated agency action, and a network map of the overlaps
- **Beat the market?** — market-adjusted returns on each priced trade vs. the S&P 500
- **Leaderboards** — who discloses most, holds most, and files late
- **Methodology** — how the data was extracted (OCR + a vision-language model for the President's scanned filings), matched, checked, and its known limits

## Data sources

Official filings from the [U.S. Office of Government Ethics](https://extapps2.oge.gov/201/Presiden.nsf) (public domain), enriched with [USASpending.gov](https://www.usaspending.gov) contract awards, [SEC EDGAR](https://www.sec.gov/edgar) tickers, the [Federal Register](https://www.federalregister.gov) for dated agency actions, and daily prices from Yahoo Finance.

---

Spot an error? [Open an issue](https://github.com/wongpeiting/who-trades-what/issues) or email pw2635@columbia.edu.
