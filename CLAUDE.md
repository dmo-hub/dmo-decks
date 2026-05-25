# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A set of Python scripts that scrape **dmo.gameking.com** (Digimon Masters Online news site) to detect game updates — currently "New Deck" and "New Digimon" announcements — across `EventView` and `PatchNote` posts. Reports are published as static HTML under `docs/` and served as GitHub Pages. Not a package — just scripts run directly from the repo root.

The site is structured as a hub: `docs/index.html` is a landing page linking to topic-specific reports (`docs/decks.html`, `docs/digimon.html`, and future ones like `docs/system.html`).

## Common commands

```powershell
# 1. Full scrape + parse (network) — populates cache/ and writes scan_result.json
python scan_decks.py

# 2. Re-parse only from cached HTML (no network) — use after tweaking parser logic
python reparse_cache.py

# 3. Inspect Digimon List / Effect tables for specific cached posts
python extract_deck_detail.py event 635 770 patch 4148

# 4. Compare scan_result.json against docs/decks.html (find missed/extra posts)
python diff_report.py

# 5. Scan cache for "[New Digimon ...]" markers → scan_result_digimon.json
python scan_digimon.py

# 6. Extract banner image per post → docs/img/digimon/<idx>.<ext>; updates JSON's `image` field
python extract_digimon_images.py

# 7. Generate docs/digimon.html from scan_result_digimon.json (uses `image` if present)
python build_digimon_html.py

# 8. Scrape KR news board list (digimonmasters.com Btype=Update) → kr_news_index.json
python fetch_kr_news_index.py

# 9. Fetch each KR update post body & extract `[ 신규 디지몬 추가 - <name> ]` markers
#    → kr_digimon_releases.json (the authoritative KR-release list)
python scan_kr_digimon_releases.py

# 10. Match EN ↔ KR by content (EN→KR keyword dict + date tiebreaker)
#     → adds `source_kr` to scan_result_digimon.json
python enrich_digimon_kr.py

# 10b. Extract KR-side digimon image from each KR post body → docs/img/digimon/<idx>_kr.<ext>
#      Adds `image_kr` field. build_digimon_html.py renders EN + KR images side-by-side
#      so a human can pick the better one later.
python extract_kr_digimon_images.py

# 11. Fetch dmowiki.com digimon pages via CDP (Cloudflare-blocked, needs a
#     Chrome session past CAPTCHA). Launch Chrome first:
#       chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\temp\chrome-cdp
#     then open https://dmowiki.com, solve the CAPTCHA, then:
python fetch_dmowiki_digimon.py
#     Saves to cache/dmowiki_<safe-slug>.html.

# 12. Parse cache/dmowiki_*.html and seed `attributes` dict on each digimon
#     in scan_result_digimon.json.
python enrich_digimon_attributes.py            # missing only
python enrich_digimon_attributes.py --force    # re-parse every digimon

# 13. Pull Basic/Natural Attribute + Affiliated Field straight from the
#     gameking EventView/PatchNote stat block (and KR `cache/kr_view_o<N>.html`
#     fallback for posts without a gameking translation, e.g. e664). This is
#     the in-game-canonical source — its values override the dmowiki seed
#     from #12 where present.
python enrich_digimon_gameking.py

# 14. Audit: dump attribute/element/families from gameking, KR, and dmowiki
#     side-by-side per digimon so divergences are easy to spot.
python compare_digimon_sources.py              # all digimon
python compare_digimon_sources.py 731          # just one idx
```

**Trusted-sources policy:** only `dmowiki.com`, gameking EventView/PatchNote,
and the KR site (digimonmasters.com) are trusted for digimon stats.
`digitalmastersworld.wiki.gg` (formerly cached as `cache/dmw_*.html`) is
**blocklisted** — its Awaken/Extreme pages return base-form data that
disagrees with the game. Do not re-introduce it.

There is no test suite, lint config, package manifest, or virtualenv setup. Only runtime dep is `requests`.

## Architecture

The three scripts form a pipeline; understanding their data flow matters more than any single file:

```
scan_decks.py ──┐
                ├──► cache/{event,patch}_<idx>.html  (raw HTML, persisted)
                └──► scan_result.json                (parsed deck names per post)
                         │
                         ├──► diff_report.py ──► diff.json  (vs. docs/decks.html)
                         │
                         └──► (manual hand-curation) ──► docs/decks.html  (deck report, published)

cache/*.html ──► scan_digimon.py ──► scan_result_digimon.json
                          │                    │
                          │                    └──► extract_digimon_images.py
                          │                                    │
                          │                                    ├──► docs/img/digimon/<idx>.<ext>
                          │                                    └──► (adds `image` field to JSON)
                          │                    │
                          │                    └──► build_digimon_html.py ──► docs/digimon.html
                          │                                                       (digimon report, auto-generated)
                          │
                          └──► enrich_digimon_kr.py (content-matches via EN→KR keyword dict)
                                                    │
                                                    └──► (adds `source_kr` field to scan_result_digimon.json)

fetch_kr_news_index.py ──► cache/kr_list_p<N>.html  (raw KR list pages)
                       └──► kr_news_index.json     (date-indexed list of KR Update posts)
                                                    │
                                                    ▼
                              scan_kr_digimon_releases.py
                                  │
                                  ├──► cache/kr_view_o<N>.html   (raw KR post bodies)
                                  └──► kr_digimon_releases.json  (KR posts w/ `신규 디지몬` markers)

docs/index.html  (hand-written landing page linking to decks.html + digimon.html)

reparse_cache.py: rebuilds scan_result.json from cache/ without network
extract_deck_detail.py: ad-hoc inspector for a single post's tables
```

Key design points:

- **`cache/` is the source of truth for parser iteration.** `scan_decks.py` fetches a detail page once and writes the raw HTML there; subsequent runs short-circuit on `cache_file.exists()`. When tweaking parsing, run `reparse_cache.py` rather than re-hitting the server.
- **Enumeration vs. detail are separate phases.** `enumerate_idx()` pages an AJAX endpoint (`AjaxEventList.aspx` / `AjaxPatchNoteList.aspx`) to discover idx values; `fetch_detail()` then GETs each `EventView.aspx?idx=…` / `PatchNoteView.aspx?idx=…` in a 15-worker thread pool.
- **Deck detection logic lives in `parse_decks()` in [scan_decks.py](scan_decks.py).** It strips HTML to plain text, finds positions of `[New Deck Add(ed)]` and `[Existing Deck Effect Changed]` / `[Modify Existing Deck]` markers, then walks every `[<Name>] Digimon List` anchor and classifies each by the *nearest preceding* marker. Don't move classification logic elsewhere — `reparse_cache.py` imports `parse_decks` and `html_to_text` directly from `scan_decks`.
- **`extract_deck_detail.py` uses a different, table-aware parser** (finds the next `<table>` after each heading). It exists because `parse_decks()` only captures deck names, not the Digimon List / Effect tables.
- **KR is a secondary reference source, matched by content (not date).** Posts in `scan_result_digimon.json` carry both a `source` (typically `dmo.gameking.com`, the English translation) and an optional `source_kr` (`digimonmasters.com`, the original Korean post). `build_digimon_html.py` renders both links with `EN`/`KR` labels (auto-detected by hostname). The matching pipeline is content-based because gameking-side translations can lag KR by anywhere from 1 day to several months (e.g. e673 Kuzuhamon = 28-day lag, e663 Omegamon Merciful = 3-month lag — pure date matching is unreliable):
  1. [scan_kr_digimon_releases.py](scan_kr_digimon_releases.py) fetches every KR Update post body and extracts `[ 신규 디지몬 (계열)? (추가)? - <name> ]` markers using balanced-bracket walking (names can contain nested `[각성]` / `[극의]` prefixes). Output: `kr_digimon_releases.json`.
  2. [enrich_digimon_kr.py](enrich_digimon_kr.py) maps EN digimon names to KR keywords via the `EN_TO_KR_KEYWORDS` list (ordered: longer/more-specific keys first, so "Abbadomon Core" matches before "Abbadomon"), then looks up each keyword in the KR release list. If multiple KR posts contain the keyword, the one closest to the gameking date wins.
  3. `OVERRIDES` in `enrich_digimon_kr.py` handles digimon released only via deck/event posts that lack a `신규 디지몬` marker (e.g. Omegamon Merciful Mode came in via deck "하얀 날개 : 용기의 우령도", post o=780048).
- **The deck report is hand-curated; the digimon report is auto-generated.** No script auto-generates `docs/decks.html` from `scan_result.json` — it's edited by hand because deck content includes tables (Digimon List + Effect) that need human review. `diff_report.py` reports drift between scan and report. By contrast, `docs/digimon.html` is fully generated by `build_digimon_html.py` from `scan_result_digimon.json` since digimon entries are just names + metadata. The deck report supports two layouts (old `<h2>idx N</h2>` and new `<section id="e<idx>">`) — `parse_report_idx()` handles both.

## Publishing the report

The `docs/` folder is published as **https://dmo-hub.github.io/dmo/** via GitHub Pages, configured to serve from this repo's `main` branch / `/docs` folder. Repo is `dmo-hub/dmo` (previously `dmoDeck` / `dmo-decks` — both old URLs auto-redirect). Edit files under `docs/`, commit, push to `origin/main` (SSH key at `~/.ssh/id_ed25519_github`), and Pages rebuilds in ~30s.

```bash
# After editing/regenerating files in docs/
git add docs/ && git commit -m "update report" && git push
```

To add a new report type (e.g. `system.html` for game-system updates), add a card to `docs/index.html` linking to it and create `docs/<topic>.html` with the same look-and-feel as `decks.html` / `digimon.html` (shared CSS inline in each file).

## Conventions worth knowing

- All scripts force UTF-8 stdout at startup (`sys.stdout.reconfigure`) because the project path contains Thai characters and the default Windows console encoding will crash on prints.
- `BASE` host, the two AJAX endpoints, and the two view-URL templates are centralized in the `CONFIGS` dict at the top of [scan_decks.py](scan_decks.py) — other scripts import from there rather than duplicating URLs.
- Post dates in cached HTML are `MM-DD-YYYY` (US format), extracted with `DATE_RE = r">\s*(\d{2}-\d{2}-\d{4})\s*<"`.
