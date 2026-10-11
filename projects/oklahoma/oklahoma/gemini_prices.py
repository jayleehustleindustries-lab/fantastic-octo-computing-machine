"""Snapshot Gemini WNBA prediction-market prices to a CSV. Free, public, read-only.

    python -m oklahoma.gemini_prices                  # fetch live prices, append to data/market_prices.csv
    python -m oklahoma.gemini_prices --from-file x.json   # parse a saved response (offline / testing)
    python -m oklahoma.gemini_prices --show           # also print the table

No API key is needed: this reads public market data only. It never places orders.
Run it twice a day (e.g. cron) or whenever you want a price snapshot.

ENDPOINT NOTE: the URL below was NOT verified from the development environment (Gemini
was blocked there). The response parser WAS tested on real data returned by Gemini's
prediction-market listing. If the fetch fails, check Gemini's prediction-markets API
docs for the "list events" URL and set GEMINI_EVENTS_URL (env var) or pass --url.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "data" / "market_prices.csv"
DEFAULT_URL = "https://api.gemini.com/v1/prediction-markets/events"   # UNVERIFIED, see module docstring
CHAMPION_TICKER = "WNBA26CHAMP"

FIELDS = [
    "captured_at", "event_ticker", "event_title", "market_type", "expiry", "contract_ticker",
    "label", "best_bid", "best_ask", "last_trade", "mid", "spread",
]


def _num(x):
    try:
        return None if x in (None, "") else float(x)
    except (TypeError, ValueError):
        return None


def market_type(event_ticker: str) -> str | None:
    """'moneyline' for single WNBA games, 'champion' for the title market, else None."""
    if event_ticker == CHAMPION_TICKER:
        return "champion"
    if event_ticker.startswith("WNBA-") and event_ticker.endswith("-M"):
        return "moneyline"
    return None


def extract_events(payload) -> list[dict]:
    """Accept {"data": [...]}, {"events": [...]} or a bare list."""
    if isinstance(payload, list):
        return payload
    for key in ("data", "events"):
        if isinstance(payload, dict) and isinstance(payload.get(key), list):
            return payload[key]
    raise ValueError("unrecognised response shape: expected a list or a 'data'/'events' list")


def parse(payload, captured_at: str | None = None) -> list[dict]:
    """Rows for every open WNBA game / champion contract that has a price. Never invents prices."""
    captured_at = captured_at or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    rows = []
    for ev in extract_events(payload):
        ticker = str(ev.get("ticker", ""))
        mtype = market_type(ticker)
        if mtype is None or ev.get("status") not in (None, "active"):
            continue
        for c in ev.get("contracts", []):
            if c.get("marketState") != "open":
                continue
            p = c.get("prices") or {}
            bid, ask, last = _num(p.get("bestBid")), _num(p.get("bestAsk")), _num(p.get("lastTradePrice"))
            if bid is None and ask is None:
                continue
            both = bid is not None and ask is not None
            rows.append({
                "captured_at": captured_at, "event_ticker": ticker, "event_title": ev.get("title", ""),
                "market_type": mtype, "expiry": ev.get("expiryDate", ""), "contract_ticker": c.get("ticker", ""),
                "label": c.get("label", ""), "best_bid": bid, "best_ask": ask, "last_trade": last,
                "mid": round((bid + ask) / 2, 4) if both else None,
                "spread": round(ask - bid, 4) if both else None,
            })
    return rows


def fetch(url: str, timeout: int = 30) -> dict | list:
    q = urllib.parse.urlencode({"search": "WNBA", "status": "active", "limit": 100})
    req = urllib.request.Request(f"{url}?{q}", headers={"User-Agent": "oklahoma-research/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def append_csv(rows: list[dict], path: pathlib.Path = OUT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default=os.environ.get("GEMINI_EVENTS_URL", DEFAULT_URL))
    ap.add_argument("--from-file", help="parse a saved JSON response instead of fetching")
    ap.add_argument("--out", default=str(OUT_PATH))
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    try:
        payload = json.load(open(args.from_file)) if args.from_file else fetch(args.url)
        rows = parse(payload)
    except Exception as e:  # noqa: BLE001 - report any fetch/parse failure plainly
        print(f"ERROR: {e}\nIf this is a fetch error, the endpoint URL may be wrong: see the module docstring.", file=sys.stderr)
        return 1
    if not rows:
        print("no active WNBA markets with prices (off-season, or between rounds): nothing saved")
        return 0
    append_csv(rows, pathlib.Path(args.out))
    print(f"saved {len(rows)} prices from {len({r['event_ticker'] for r in rows})} events -> {args.out}")
    if args.show:
        for r in rows:
            print(f"{r['event_title'][:34]:34s} {r['label'][:14]:14s} bid {r['best_bid']}  ask {r['best_ask']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
