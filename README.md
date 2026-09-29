# 200MA widget backend

Daily GitHub Action computes SMA/EMA 200 for the tickers in `ma200.py`, writes
`docs/<ticker>.json`, and optionally pushes an ntfy notification when the signal flips.

## Setup
1. Create a GitHub repo (public, so Pages and raw URLs work) and push these files.
2. Settings → Pages → Source: *Deploy from a branch*, branch `main`, folder `/docs`.
3. Actions tab → *Update 200MA signal* → *Run workflow* once to test.
4. Optional push alerts: install the ntfy app, subscribe to a hard-to-guess topic
   (e.g. `felix-ma200-x7k2`), and add it as repo secret `NTFY_TOPIC`.

JSON URL: `https://<user>.github.io/<repo>/h4zj.json`

## KWGT formulas
Add Text items and use e.g.:

    $wg("https://<user>.github.io/<repo>/h4zj.json", json, ".signal")$
    $wg("https://<user>.github.io/<repo>/h4zj.json", json, ".close")$
    SMA200 $wg("https://<user>.github.io/<repo>/h4zj.json", json, ".sma200")$
    $wg("https://<user>.github.io/<repo>/h4zj.json", json, ".dist_sma_pct")$ %

Background colour: in a Shape's Paint colour, press the formula button and use
`$wg("…/h4zj.json", json, ".color")$`.
Set Global Settings → Update → refresh interval to 1–2 hours (data changes once a day).

## Tweaks
- More tickers: add entries to `TICKERS` (e.g. `"EUNL.DE": "iShares Core MSCI World"`).
- Buffer: `MA_BUFFER` in the workflow (0 = pure cross, 0.02 = exit 2 % below SMA).
- Note: GitHub disables scheduled workflows after 60 days without repo activity;
  the daily commit keeps it alive.
