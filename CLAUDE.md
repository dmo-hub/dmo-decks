# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A small set of Python scripts that scrape **dmo.gameking.com** (Digimon Masters Online news site) to detect "New Deck Add" announcements across `EventView` and `PatchNote` posts, and renders them into a static HTML report (`new_deck_report.html`). Not a package — just scripts run directly from the repo root.

## Common commands

```powershell
# 1. Full scrape + parse (network) — populates cache/ and writes scan_result.json
python scan_decks.py

# 2. Re-parse only from cached HTML (no network) — use after tweaking parser logic
python reparse_cache.py

# 3. Inspect Digimon List / Effect tables for specific cached posts
python extract_deck_detail.py event 635 770 patch 4148

# 4. Compare scan_result.json against new_deck_report.html (find missed/extra posts)
python diff_report.py
```

There is no test suite, lint config, package manifest, or virtualenv setup. Only runtime dep is `requests`.

## Architecture

The three scripts form a pipeline; understanding their data flow matters more than any single file:

```
scan_decks.py ──┐
                ├──► cache/{event,patch}_<idx>.html  (raw HTML, persisted)
                └──► scan_result.json                (parsed deck names per post)
                         │
                         ├──► diff_report.py ──► diff.json  (vs. new_deck_report.html)
                         │
                         └──► (manual) ──► new_deck_report.html  (the published report)

reparse_cache.py: rebuilds scan_result.json from cache/ without network
extract_deck_detail.py: ad-hoc inspector for a single post's tables
```

Key design points:

- **`cache/` is the source of truth for parser iteration.** `scan_decks.py` fetches a detail page once and writes the raw HTML there; subsequent runs short-circuit on `cache_file.exists()`. When tweaking parsing, run `reparse_cache.py` rather than re-hitting the server.
- **Enumeration vs. detail are separate phases.** `enumerate_idx()` pages an AJAX endpoint (`AjaxEventList.aspx` / `AjaxPatchNoteList.aspx`) to discover idx values; `fetch_detail()` then GETs each `EventView.aspx?idx=…` / `PatchNoteView.aspx?idx=…` in a 15-worker thread pool.
- **Deck detection logic lives in `parse_decks()` in [scan_decks.py](scan_decks.py).** It strips HTML to plain text, finds positions of `[New Deck Add(ed)]` and `[Existing Deck Effect Changed]` / `[Modify Existing Deck]` markers, then walks every `[<Name>] Digimon List` anchor and classifies each by the *nearest preceding* marker. Don't move classification logic elsewhere — `reparse_cache.py` imports `parse_decks` and `html_to_text` directly from `scan_decks`.
- **`extract_deck_detail.py` uses a different, table-aware parser** (finds the next `<table>` after each heading). It exists because `parse_decks()` only captures deck names, not the Digimon List / Effect tables.
- **The HTML report is currently hand-curated.** No script auto-generates `new_deck_report.html` from `scan_result.json`; `diff_report.py` only reports drift between them. The report supports two layouts (old `<h2>idx N</h2>` and new `<section id="e<idx>">`) — `parse_report_idx()` handles both.

## Publishing the report

`new_deck_report.html` is mirrored to **https://dmo-hub.github.io/dmo-decks/** (GitHub Pages, repo `dmo-hub/dmo-decks`). The local working clone of that mirror lives at `C:\Users\kongp\AppData\Local\Temp\dmo-decks-deploy\` (a.k.a. `/tmp/dmo-decks-deploy/` in git-bash).

```bash
# After editing new_deck_report.html, mirror to the Pages repo and push
cp new_deck_report.html /tmp/dmo-decks-deploy/index.html
cd /tmp/dmo-decks-deploy
git add index.html && git commit -m "update" && git push
# ↑ SSH auth via ~/.ssh/id_ed25519_github; Pages rebuilds in ~30s
```

The Pages repo is a separate one-way mirror — `index.html` there is just a renamed copy of `new_deck_report.html` here. If the working dir is missing (Windows tmp can be cleared), re-clone with `git clone git@github.com:dmo-hub/dmo-decks.git`.

## Conventions worth knowing

- All scripts force UTF-8 stdout at startup (`sys.stdout.reconfigure`) because the project path contains Thai characters and the default Windows console encoding will crash on prints.
- `BASE` host, the two AJAX endpoints, and the two view-URL templates are centralized in the `CONFIGS` dict at the top of [scan_decks.py](scan_decks.py) — other scripts import from there rather than duplicating URLs.
- Post dates in cached HTML are `MM-DD-YYYY` (US format), extracted with `DATE_RE = r">\s*(\d{2}-\d{2}-\d{4})\s*<"`.
