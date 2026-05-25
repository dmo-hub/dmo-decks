"""Fetch Basic Attribute / Natural Attribute / Field for each digimon and
add them to scan_result_digimon.json.

Sources tried, in order:
  1. cache/dmowiki_<slug>.html   — fetched manually via fetch_dmowiki_digimon.py
                                    (CDP/Playwright since dmowiki.com is behind CF)
  2. https://digitalmastersworld.wiki.gg/wiki/<slug>  — plain requests, no CF

Fields extracted:
  - attribute            "Vaccine" / "Virus" / "Data" / "Free"
  - natural_attribute    "Light" / "Fire" / "Wood" / ... (element)
  - families             ["Virus Busters", "Wind Guardians", ...] (fields)

dmw cache files live at cache/dmw_<slug>.html so reruns are cheap.

The result is attached per-digimon as a parallel `attributes` dict on each
post so existing readers that expect `digimon: list[str]` still work:

    "663": {
      ...,
      "digimon": ["Omegamon – Merciful Mode"],
      "attributes": {
        "Omegamon – Merciful Mode": {
          "attribute": "Vaccine",
          "attribute_abbr": "VA",
          "natural_attribute": "Light",
          "families": ["Virus Busters", "Wind Guardians", "Metal Empire"]
        }
      }
    }

Usage:
  python enrich_digimon_attributes.py            # missing only
  python enrich_digimon_attributes.py --force    # re-fetch every digimon
"""

import json
import re
import sys
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

PROJ = Path(__file__).resolve().parent
SCAN = PROJ / "scan_result_digimon.json"
CACHE = PROJ / "cache"
CACHE.mkdir(exist_ok=True)

WIKI = "https://digitalmastersworld.wiki.gg/wiki"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}

ABBR = {"Vaccine": "VA", "Virus": "VI", "Data": "DA", "Free": "FR"}

BASIC_ATTRS = {"Vaccine", "Virus", "Data", "Free"}
# Natural attributes (elements) seen on dmwiki. Categories named
# "<Name> Attribute" that fall outside BASIC_ATTRS land here.
NATURAL_ATTRS = {
    "Fire", "Water", "Earth", "Wind", "Wood", "Light",
    "Steel", "Thunder", "Pitch Black", "Neutral",
}
# Known digimon family / "Field" names (used to split categories).
FAMILIES = {
    "Virus Busters", "Wind Guardians", "Nightmare Soldiers", "Jungle Troopers",
    "Nature Spirits", "Deep Savers", "Metal Empire", "Dragon's Roar",
    "Unknown", "Dark Area",
}

# Manual name → DMW slug overrides for pages whose URL can't be derived from
# the gameking name (different parenthesization, alt spelling, etc.). Append
# new entries as new digimon are released.
OVERRIDES: dict[str, str] = {
    "Imperialdramon Paladin Mode (Awaken)": "Imperialdramon_(Paladin_Mode)",
    "Bloomlordmon": "BloomLordmon",
    "Omegamon X Extreme": "Omegamon_X",
    "Gallantmon Crimson Mode": "Gallantmon_(Crimson_Mode)",
    "Kuzuhamon MikoMode": "Kuzuhamon_Miko_Mode",
}


def name_candidates(raw_name: str) -> list[str]:
    """Generate DMW Wiki slug candidates from a digimon name.

    Tries:
      * the name itself
      * with leading `[X]` / `(X)` qualifier stripped (e.g. "[Extreme] X")
      * with trailing `(X)` / `[X]` qualifier stripped (e.g. "X (Awaken)")
      * with both stripped
    Each source name is then converted to slug form, with two paren-handling
    variants (keep / drop parens) — mirrors fetch_dmw_images convention.
    """
    sources = {raw_name}
    no_lead = re.sub(r"^\s*[\[(][^\])]+[\])]\s*", "", raw_name).strip()
    no_trail = re.sub(r"\s*[\[(][^\])]+[\])]\s*$", "", raw_name).strip()
    no_both = re.sub(r"\s*[\[(][^\])]+[\])]\s*$", "", no_lead).strip()
    for s in (no_lead, no_trail, no_both):
        if s:
            sources.add(s)

    candidates: list[str] = []
    for s in sources:
        # keep parens (matches "Foo_(Bar)")
        a = re.sub(r"[\-–—:\[\]]", " ", s)
        a = re.sub(r"\s+", " ", a).strip().replace(" ", "_")
        # drop parens too
        b = re.sub(r"[\-–—:\[\]()]", " ", s)
        b = re.sub(r"\s+", " ", b).strip().replace(" ", "_")
        candidates.extend([a, b])

    seen, out = set(), []
    for v in candidates:
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def fetch_page(slug: str) -> str | None:
    """Fetch a wiki page, using a per-slug cache. Returns None if not found."""
    cache_file = CACHE / f"dmw_{slug}.html"
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")
    url = f"{WIKI}/{slug}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
    except Exception as e:
        print(f"    ! fetch error: {e}")
        return None
    if r.status_code != 200:
        return None
    # MediaWiki returns 200 with "noarticletext" for missing pages — detect it.
    if "noarticletext" in r.text or "There is currently no text in this page" in r.text:
        return None
    cache_file.write_text(r.text, encoding="utf-8")
    return r.text


def strip_tags(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def parse_dmowiki(html: str) -> dict | None:
    """Parse a dmowiki.com page (saved via Playwright/CDP). Both wikis are
    MediaWiki, so we first try the same scraper-digimon-* infobox ids, and
    fall back to MediaWiki categories (wgCategories JSON in RLCONF) which
    dmowiki tags every digimon page with — e.g. "Vaccine Attribute",
    "Light Attribute", "Virus Busters".
    """
    # 1) infobox path — works if dmowiki uses the same template structure
    via_infobox = parse_attributes(html)
    if via_infobox:
        return via_infobox

    # 2) wgCategories path
    m = re.search(r'"wgCategories":\[([^\]]+)\]', html)
    if not m:
        return None
    cats = [c.strip().strip('"') for c in m.group(1).split(",")]

    result: dict = {}
    for c in cats:
        if c.endswith(" Attribute"):
            name = c[: -len(" Attribute")].strip()
            if name in BASIC_ATTRS:
                result["attribute"] = name
                if name in ABBR:
                    result["attribute_abbr"] = ABBR[name]
            elif name in NATURAL_ATTRS or name not in BASIC_ATTRS:
                # Treat any "<X> Attribute" that isn't basic as natural.
                result.setdefault("natural_attribute", name)
        elif c in FAMILIES:
            result.setdefault("families", []).append(c)

    return result or None


def parse_attributes(html: str) -> dict | None:
    """Pull Basic Attribute, Natural Attribute, and Families from the infobox.

    Returns None if no recognizable infobox is present (i.e. the page exists
    but isn't a digimon page).
    """
    def cell_by_id(id_: str) -> str | None:
        m = re.search(rf'id="{id_}"[^>]*>(.*?)</td>', html, re.S)
        if not m:
            return None
        return strip_tags(m.group(1))

    attr = cell_by_id("scraper-digimon-attribute")
    natural = cell_by_id("scraper-digimon-naturalattribute")

    # Families row has no id; find it by label, then capture the next <td>.
    families: list[str] = []
    m = re.search(r"Families:\s*</a>\s*</b>\s*</td>\s*<td[^>]*>(.*?)</td>",
                  html, re.S)
    if m:
        cell = m.group(1)
        for fm in re.finditer(
            r'href="/wiki/Category:([^"]+)" title="Category:[^"]+">([^<]+)</a>',
            cell,
        ):
            label = fm.group(2).strip()
            if label and label not in families:
                families.append(label)

    if not (attr or natural or families):
        return None

    result: dict = {}
    if attr:
        result["attribute"] = attr
        if attr in ABBR:
            result["attribute_abbr"] = ABBR[attr]
    if natural:
        result["natural_attribute"] = natural
    if families:
        result["families"] = families
    return result


def try_dmowiki_cache(name: str) -> tuple[dict, str] | None:
    """Look for a manually-fetched dmowiki page that matches this name. Uses
    the same resolve_slug() the fetcher used (rank_u.html + OVERRIDES), so
    matching is exact — no fuzzy `in` substring traps like Abbadomon vs
    Abbadomon Core."""
    try:
        from fetch_dmowiki_digimon import (
            build_rank_u_map,
            resolve_slug,
            safe_filename,
        )
    except Exception:
        return None
    if not hasattr(try_dmowiki_cache, "_rank_map"):
        try_dmowiki_cache._rank_map = build_rank_u_map()  # type: ignore[attr-defined]
    slug = resolve_slug(name, try_dmowiki_cache._rank_map)  # type: ignore[attr-defined]
    if not slug:
        return None
    f = CACHE / f"dmowiki_{safe_filename(slug)}.html"
    if not f.exists():
        return None
    attrs = parse_dmowiki(f.read_text(encoding="utf-8"))
    if attrs:
        return attrs, slug
    return None


def lookup(name: str) -> tuple[dict, str] | None:
    """First check a dmowiki CDP-fetched cache, then try DMW Wiki candidates."""
    hit = try_dmowiki_cache(name)
    if hit:
        print(f"    ✓ dmowiki:{hit[1]} → {hit[0]}")
        return hit

    slugs: list[str] = []
    if name in OVERRIDES:
        slugs.append(OVERRIDES[name])
    slugs.extend(s for s in name_candidates(name) if s not in slugs)

    for slug in slugs:
        html = fetch_page(slug)
        if html is None:
            print(f"    ✗ dmw:{slug} (no page)")
            continue
        attrs = parse_attributes(html)
        if attrs:
            print(f"    ✓ dmw:{slug} → {attrs}")
            return attrs, slug
        unrel = "not released yet" in html
        print(f"    ✗ dmw:{slug} ({'unreleased' if unrel else 'no infobox'})")
    return None


def main() -> None:
    force = "--force" in sys.argv
    data = json.loads(SCAN.read_text(encoding="utf-8"))

    updated = 0
    missing: list[str] = []
    for kind in ("event", "patch"):
        for idx, post in data.get(kind, {}).items():
            existing = post.get("attributes") or {}
            new_attrs = dict(existing) if not force else {}
            for name in post["digimon"]:
                if name in new_attrs and not force:
                    continue
                print(f"\n{kind}_{idx}: {name}")
                hit = lookup(name)
                if hit:
                    new_attrs[name] = hit[0]
                    updated += 1
                else:
                    missing.append(f"{kind} {idx}: {name}")
            if new_attrs:
                post["attributes"] = new_attrs

    SCAN.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    print(f"\n--- Updated {updated} digimon entries in {SCAN.name} ---")
    if missing:
        print(f"--- {len(missing)} entries had no DMW Wiki match: ---")
        for m in missing:
            print(f"  {m}")


if __name__ == "__main__":
    main()
