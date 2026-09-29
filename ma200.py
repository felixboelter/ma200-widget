"""
Compute 200-day SMA/EMA trend signals and write one flat JSON file per ticker
into docs/, where GitHub Pages serves it to a KWGT widget.

Signal logic (with hysteresis to cut whipsaws):
  OUT  when the daily close falls below SMA200 * (1 - BUFFER)
  IN   when the daily close rises back above SMA200
Optionally sends a push via ntfy.sh when the signal flips on the latest close.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
import yfinance as yf

TICKERS = {
    # yfinance symbol: display name
    "H4ZJ.DE": "HSBC MSCI World",
}
BUFFER = float(os.getenv("MA_BUFFER", "0.02"))  # 2 % below SMA to exit
WINDOW = 200
OUT_DIR = Path("docs")
NTFY_TOPIC = os.getenv("NTFY_TOPIC")  # set as a repo secret to enable pushes


def compute(symbol: str, name: str) -> dict:
    df = yf.Ticker(symbol).history(period="3y", auto_adjust=True)
    close = df["Close"].dropna()
    if len(close) < WINDOW + 1:
        raise RuntimeError(f"{symbol}: only {len(close)} closes, need {WINDOW + 1}")

    sma = close.rolling(WINDOW).mean()
    ema = close.ewm(span=WINDOW, adjust=False).mean()

    # Walk the history once to get a stateful signal with hysteresis.
    signal, since, prev_signal = "IN", None, "IN"
    for date, c, s in zip(close.index, close, sma):
        if s != s:  # NaN during warm-up
            continue
        prev_signal = signal
        if signal == "IN" and c < s * (1 - BUFFER):
            signal = "OUT"
        elif signal == "OUT" and c > s:
            signal = "IN"
        if signal != prev_signal or since is None:
            since = date
    flipped_today = signal != prev_signal

    last_close, last_sma, last_ema = close.iloc[-1], sma.iloc[-1], ema.iloc[-1]
    dist = (last_close / last_sma - 1) * 100
    exit_level = last_sma * (1 - BUFFER)
    headroom = (last_close / exit_level - 1) * 100  # % the price can fall before OUT
    de = lambda x, n=2: f"{x:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    is_in = signal == "IN"
    return {
        "symbol": symbol,
        "name": name,
        "date": close.index[-1].strftime("%Y-%m-%d"),
        "close": round(float(last_close), 3),
        "sma200": round(float(last_sma), 3),
        "ema200": round(float(last_ema), 3),
        "dist_sma_pct": round(float((last_close / last_sma - 1) * 100), 2),
        "dist_ema_pct": round(float((last_close / last_ema - 1) * 100), 2),
        "exit_level": round(float(last_sma * (1 - BUFFER)), 3),
        "buffer_pct": BUFFER * 100,
        "signal": signal,
        "signal_since": since.strftime("%Y-%m-%d"),
        "flipped_today": flipped_today,
        "color": "#2E7D32" if is_in else "#C62828",
        # Pre-formatted fields for the widget
        "close_fmt": f"{de(last_close)} €",
        "sma_fmt": de(last_sma),
        "dist_fmt": f"{'+' if dist >= 0 else '−'}{de(abs(dist), 1)} %",
        "headroom_fmt": f"{de(headroom, 1)} %" if is_in else "–",
        "bar_pct": int(max(0, min(100, headroom / 15 * 100))) if is_in else 0,
        "arrow": "▲" if dist >= 0 else "▼",
        "accent": "#4ADE80" if is_in else "#F87171",
        "accent_dim": "#1A4ADE80" if is_in else "#1AF87171",
        "bg": "#E6111827",
        "muted": "#9CA3AF",
        "updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
    }


def notify(d: dict) -> None:
    if not NTFY_TOPIC or not d["flipped_today"]:
        return
    msg = (f"{d['name']}: signal now {d['signal']} "
           f"(close {d['close']}, SMA200 {d['sma200']}, {d['dist_sma_pct']:+.2f}%)")
    requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=msg.encode(),
                  headers={"Title": "200MA cross", "Priority": "high"}, timeout=10)


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for symbol, name in TICKERS.items():
        data = compute(symbol, name)
        slug = symbol.split(".")[0].lower()
        (OUT_DIR / f"{slug}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        notify(data)
        print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
