"""Match each entry in scan_result_digimon.json to a KR update post by date
(±MAX_DAYS) and add a `source_kr` field.

Reads:  scan_result_digimon.json + kr_news_index.json
Writes: scan_result_digimon.json (in place — only adds/updates `source_kr`)

Matching:
- Only consider KR posts with type == "update" (skip promotion-only posts).
- Closest-date wins; ties prefer the KR post on or before the EN date
  (gameking translates KR with a typical 0–2 day lag).
- Posts already pointing to a digimonmasters.com source URL keep that URL.
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJ = Path(__file__).resolve().parent
DIGIMON = PROJ / "scan_result_digimon.json"
KR_INDEX = PROJ / "kr_news_index.json"

MAX_DAYS = 3  # search window for date-based matching


def parse_mmddyyyy(s: str) -> date:
    mm, dd, yyyy = s.split("-")
    return date(int(yyyy), int(mm), int(dd))


def parse_iso(s: str) -> date:
    y, m, d = s.split("-")
    return date(int(y), int(m), int(d))


def best_kr_match(en_date: date, kr_updates: list[dict]) -> dict | None:
    """Find the KR update post closest to en_date within ±MAX_DAYS.

    Tie-break: prefer KR post on/before en_date (typical gameking lag).
    """
    candidates = []
    for k in kr_updates:
        kd = parse_iso(k["date"])
        diff = (en_date - kd).days  # positive if KR is earlier than EN
        if abs(diff) <= MAX_DAYS:
            # sort key: (absolute distance, prefer earlier KR ⇒ smaller abs(diff) with diff>=0 first)
            candidates.append((abs(diff), -diff, k))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], -x[1]))
    return candidates[0][2]


def main() -> None:
    data = json.loads(DIGIMON.read_text(encoding="utf-8"))
    kr = json.loads(KR_INDEX.read_text(encoding="utf-8"))
    kr_updates = [p for p in kr["posts"] if p["type"] == "update"]

    matched = 0
    skipped_existing = 0
    unmatched = []

    for kind in ("event", "patch"):
        for idx, post in data.get(kind, {}).items():
            # Skip if `source` is already a digimonmasters.com URL — it's already KR.
            existing_src = post.get("source", "")
            if "digimonmasters.com" in existing_src and "source_kr" not in post:
                post["source_kr"] = existing_src
                skipped_existing += 1
                continue

            en_date = parse_mmddyyyy(post["date"])
            match = best_kr_match(en_date, kr_updates)
            if match:
                post["source_kr"] = match["url"]
                matched += 1
                lag = (en_date - parse_iso(match["date"])).days
                print(f"  {kind} {idx} ({post['date']}) → KR o={match['o']} "
                      f"({match['date']}, lag {lag:+d}d): {match['title'][:60]}")
            else:
                unmatched.append(f"{kind} {idx} ({post['date']})")

    DIGIMON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nMatched: {matched}, existing KR source kept: {skipped_existing}, "
          f"unmatched: {len(unmatched)}")
    for u in unmatched:
        print(f"  unmatched: {u}")


if __name__ == "__main__":
    main()
