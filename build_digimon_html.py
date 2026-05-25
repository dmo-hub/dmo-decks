"""Generate docs/digimon.html from scan_result_digimon.json.

Re-run after scan_digimon.py to refresh the published Digimon report.
"""

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJ = Path(__file__).resolve().parent
SRC = PROJ / "scan_result_digimon.json"
KR_INDEX = PROJ / "kr_news_index.json"
OUT = PROJ / "docs" / "digimon.html"


def fmt_date(mmddyyyy: str | None) -> str:
    """MM-DD-YYYY → DD.MM.YYYY (matches deck report convention)."""
    if not mmddyyyy:
        return ""
    mm, dd, yyyy = mmddyyyy.split("-")
    return f"{dd}.{mm}.{yyyy}"


def fmt_iso_date(iso: str | None) -> str:
    """YYYY-MM-DD → DD.MM.YYYY."""
    if not iso:
        return ""
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


def canonical_src_key(url: str) -> tuple[str, str]:
    """Canonical (kind, id) per source URL, so two URLs pointing to the same
    KR post (different query-string order) dedupe correctly."""
    if "digimonmasters.com" in url:
        m = re.search(r"[?&]o=(\d+)", url)
        return ("kr", m.group(1) if m else url)
    if "gameking.com" in url:
        m = re.search(r"[?&]idx=(\d+)", url)
        return ("na", m.group(1) if m else url)
    return ("other", url)


CSS = """
  * { box-sizing: border-box; }
  body { font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; margin: 0; color: #2c3e50; background: #f5f7fa; line-height: 1.5; }
  .container { max-width: 1200px; margin: 0 auto; padding: 24px; display: grid; grid-template-columns: 240px 1fr; gap: 28px; }
  @media (max-width: 900px) { .container { grid-template-columns: 1fr; } .toc { position: static !important; max-height: none !important; } }

  /* Sidebar */
  .toc { position: sticky; top: 16px; max-height: calc(100vh - 32px); overflow-y: auto;
         background: white; border-radius: 10px; padding: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); font-size: 12.5px; }
  .toc h3 { margin: 0 0 8px 0; color: #1a4d8f; font-size: 13px; border-bottom: 2px solid #e7eef6; padding-bottom: 5px; }
  .toc h4 { margin: 10px 0 4px 0; font-size: 10.5px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
  .toc a { color: #2c3e50; text-decoration: none; display: block; padding: 3px 6px; border-radius: 4px; line-height: 1.35; }
  .toc a:hover { background: #eef4fb; color: #1a4d8f; }
  .toc .nav-home { display: inline-block; font-size: 11px; color: #2c6fb8; padding: 0; margin-bottom: 8px; }
  .toc .nav-home:hover { text-decoration: underline; }

  /* Hero header */
  .hero { background: linear-gradient(135deg, #1a4d8f, #2c6fb8); border-radius: 10px; padding: 18px 24px; margin-bottom: 14px;
          display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 18px;
          box-shadow: 0 4px 14px rgba(26,77,143,0.20); }
  .hero h1 { color: white; margin: 0; font-size: 22px; line-height: 1.2; letter-spacing: 0.2px; }
  .hero-stats { display: flex; gap: 22px; }
  .hero-stat { text-align: center; color: white; padding: 0 6px; }
  .hero-stat .num { font-size: 30px; font-weight: 700; line-height: 1; }
  .hero-stat .lbl { font-size: 10.5px; opacity: 0.88; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }

  /* Section headers */
  .section-title { font-size: 22px; color: #fff; background: linear-gradient(135deg, #1a4d8f, #2c6fb8); padding: 12px 18px; border-radius: 8px; margin: 32px 0 16px 0; box-shadow: 0 2px 6px rgba(26,77,143,0.2); }
  .section-title.patch { background: linear-gradient(135deg, #9b3f1a, #c0573a); box-shadow: 0 2px 6px rgba(155,63,26,0.2); }

  /* Post card */
  .post { background: white; border-radius: 10px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
  .post-header { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; margin-bottom: 4px; }
  .post-header .idx-badge { background: #1a4d8f; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
  .post-header.patch .idx-badge { background: #9b3f1a; }
  .post-header h2 { color: #2c3e50; font-size: 19px; margin: 0; }
  .post-header .date { color: #95a5a6; font-size: 13px; }
  .src { font-size: 12px; margin: 0 0 16px 0; display: flex; flex-wrap: wrap; gap: 6px 14px; align-items: center; }
  .src a { color: #2c6fb8; text-decoration: none; }
  .src a:hover { text-decoration: underline; }
  .src .src-label { color: #95a5a6; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
  .src .src-date { color: #95a5a6; font-size: 11px; margin: 0 4px; }
  .src .src-kr a { color: #c0392b; }

  /* Digimon list — orange-border cards matching deck style */
  .digimon-list { list-style: none; padding: 0; margin: 8px 0 0 0; display: grid; gap: 10px; }
  .digimon-list li { padding: 12px 18px; background: #fafbfc; border-radius: 8px; box-shadow: 0 0 0 2px #f39c12;
                     font-size: 16px; font-weight: 700; color: #1a4d8f; }
  .post.patch .digimon-list li { color: #9b3f1a; }
  .digimon-name { display: block; margin-bottom: 6px; }

  /* Attribute chips (Basic / Natural / Families) — icon + name layout */
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; font-weight: 500; font-size: 12px; }
  .chip { padding: 3px 9px 3px 4px; border-radius: 999px; line-height: 1.4; letter-spacing: 0.3px;
          display: inline-flex; align-items: center; gap: 4px; }
  .chip-icon { width: 18px; height: 18px; vertical-align: middle; object-fit: contain; flex-shrink: 0; }
  /* Basic attribute colors */
  .chip-attr-VA { background: #d6f0d6; color: #1f6b1f; }
  .chip-attr-VI { background: #efd9ef; color: #6b1f6b; }
  .chip-attr-DA { background: #d6e3f5; color: #1a4d8f; }
  .chip-attr-FR { background: #f0e4cc; color: #8a6a1a; }
  .chip-attr-UN { background: #ebebeb; color: #555; }
  /* Natural attribute (element) — neutral grey base */
  .chip-elem { background: #eef2f5; color: #2c3e50; border: 1px solid #d4dce3; }
  /* Families (was "Field") — neutral pale orange */
  .chip-families { background: #fff1d6; color: #9b6e1a; border: 1px solid #f1d49a; }

  /* Banner image (one per post) */
  .post-image { display: block; max-width: 100%; max-height: 360px; margin: 4px 0 14px 0;
                border-radius: 6px; border: 1px solid #e7eef6; cursor: zoom-in;
                object-fit: contain; }
"""


ATTR_ABBR_MAP = {"Vaccine": "VA", "Virus": "VI", "Data": "DA",
                 "Free": "FR", "Unknown": "UN"}

ELEM_ICON = {
    "Light": "Light", "Fire": "Fire", "Water": "Water", "Wind": "Wind",
    "Wood": "Wood", "Earth": "Earth", "Steel": "Steel", "Thunder": "Thunder",
    "Ice": "Ice", "Neutral": "Neutral", "Pitch Black": "Pitch_Black",
}
FAMILY_ICON = {
    "Virus Busters": "Virus_Busters",
    "Wind Guardians": "Wind_Guardians",
    "Nightmare Soldiers": "Nightmare_Soldiers",
    "Jungle Troopers": "Jungle_Troopers",
    "Nature Spirits": "Nature_Spirits",
    "Deep Savers": "Deep_Savers",
    "Metal Empire": "Metal_Empire",
    "Dragon's Roar": "Dragons_Roar",
    "Unknown": "Unknown",
    "Dark Area": "Dark_Area",
    "TBD": "TBD",
}


def render_digimon(name: str, attrs: dict | None, show_name: bool = True) -> str:
    """Render a digimon's chip row (attribute / element / families) as
    icon + name chips. Icons live in docs/img/icons/<category>-<slug>.png.

    `show_name` is False for single-digimon posts — the name is already in
    the section <h2>, so the chip row stands alone.
    """
    chips: list[str] = []
    if attrs:
        if attrs.get("attribute"):
            value = attrs["attribute"]
            abbr = attrs.get("attribute_abbr") or ATTR_ABBR_MAP.get(value, "UN")
            chips.append(
                f'<span class="chip chip-attr-{abbr}" title="Basic Attribute: {value}">'
                f'<img class="chip-icon" src="img/icons/attr-{value}.png" alt="">'
                f'{value}</span>'
            )
        if attrs.get("natural_attribute"):
            value = attrs["natural_attribute"]
            slug = ELEM_ICON.get(value, value.replace(" ", "_"))
            chips.append(
                f'<span class="chip chip-elem" title="Natural Attribute: {value}">'
                f'<img class="chip-icon" src="img/icons/elem-{slug}.png" alt="">'
                f'{value}</span>'
            )
        for fam in attrs.get("families", []):
            slug = FAMILY_ICON.get(fam, fam.replace(" ", "_"))
            chips.append(
                f'<span class="chip chip-families" title="Families: {fam}">'
                f'<img class="chip-icon" src="img/icons/field-{slug}.png" alt="">'
                f'{fam}</span>'
            )
    chip_row = f'<div class="chips">{"".join(chips)}</div>' if chips else ""
    name_html = f'<span class="digimon-name">{name}</span>' if show_name else ""
    return f"{name_html}{chip_row}" or "&nbsp;"


def render() -> str:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    events = data.get("event", {})
    patches = data.get("patch", {})

    # Per-source dates: KR posts carry their own release date (different from
    # gameking's translation date). Look up by `o` id from kr_news_index.json.
    kr_dates: dict[str, str] = {}
    if KR_INDEX.exists():
        for p in json.loads(KR_INDEX.read_text(encoding="utf-8"))["posts"]:
            kr_dates[p["o"]] = p["date"]

    total_posts = len(events) + len(patches)
    total_digimon = sum(len(p["digimon"]) for p in list(events.values()) + list(patches.values()))

    # Sort by idx ascending
    sorted_events = sorted(events.items(), key=lambda kv: int(kv[0]))
    sorted_patches = sorted(patches.items(), key=lambda kv: int(kv[0]))

    # TOC links
    toc_event_links = "\n  ".join(
        f'<a href="#e{idx}">idx {idx} — {", ".join(p["digimon"])[:50]}{"..." if len(", ".join(p["digimon"])) > 50 else ""}</a>'
        for idx, p in sorted_events
    )
    toc_patch_links = "\n  ".join(
        f'<a href="#p{idx}">idx {idx} — {", ".join(p["digimon"])[:50]}{"..." if len(", ".join(p["digimon"])) > 50 else ""}</a>'
        for idx, p in sorted_patches
    )

    def render_post(idx: str, p: dict, kind: str) -> str:
        prefix = "e" if kind == "event" else "p"
        patch_cls = " patch" if kind == "patch" else ""
        names = p["digimon"]
        n = len(names)
        attrs_map = p.get("attributes", {})
        # h2 carries the digimon name(s); only show the name in each <li>
        # when there's more than one digimon (so chip rows stay associated
        # with the right digimon).
        h2_text = ", ".join(names)
        items = "\n      ".join(
            f"<li>{render_digimon(name, attrs_map.get(name), show_name=(n > 1))}</li>"
            for name in names
        )
        img_path = p.get("image") or p.get("image_kr")
        img_block = (
            f'<a href="{img_path}" target="_blank">'
            f'<img class="post-image" src="{img_path}" alt="idx {idx}" loading="lazy">'
            f'</a>\n    '
            if img_path else ""
        )
        def src_span(url: str) -> str:
            kind, oid = canonical_src_key(url)
            is_kr = kind == "kr"
            cls = "src-kr" if is_kr else "src-en"
            label = "KR" if is_kr else "NA"
            date_str = fmt_iso_date(kr_dates.get(oid)) if is_kr else fmt_date(p["date"])
            return (
                f'<span class="{cls}"><span class="src-label">{label}</span>'
                f'<span class="src-date">{date_str}</span>'
                f'<a href="{url}" target="_blank">{url.split("/")[-1]} ↗</a></span>'
            )

        # Dedupe by canonical key — two URLs pointing to the same KR post but
        # with different query-string ordering should collapse to one entry.
        seen: set[tuple[str, str]] = set()
        src_parts: list[str] = []
        for u in (p["source"], p.get("source_kr")):
            if not u:
                continue
            key = canonical_src_key(u)
            if key in seen:
                continue
            seen.add(key)
            src_parts.append(src_span(u))
        src_html = "".join(src_parts)
        return f"""  <section class="post{patch_cls}" id="{prefix}{idx}">
    <div class="post-header{patch_cls}">
      <span class="idx-badge">idx {idx}</span>
      <h2>{h2_text}</h2>
    </div>
    <p class="src">{src_html}</p>
    {img_block}<ul class="digimon-list">
      {items}
    </ul>
  </section>
"""

    event_sections = "\n".join(render_post(idx, p, "event") for idx, p in sorted_events)
    patch_sections = "\n".join(render_post(idx, p, "patch") for idx, p in sorted_patches)

    return f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<title>DMO Digimon Report</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">

<aside class="toc">
  <a href="./" class="nav-home">← Home</a>
  <h3>สารบัญ</h3>

  <h4>EventView ({len(events)} โพสต์)</h4>
  {toc_event_links}

  <h4>PatchNote ({len(patches)} โพสต์)</h4>
  {toc_patch_links}
</aside>

<main>
  <div class="hero">
    <h1>DMO – Digimon Report</h1>
    <div class="hero-stats">
      <div class="hero-stat"><div class="num">{total_posts}</div><div class="lbl">โพสต์</div></div>
      <div class="hero-stat"><div class="num">{total_digimon}</div><div class="lbl">digimon ใหม่</div></div>
    </div>
  </div>

  <h3 class="section-title">📅 EventView Posts</h3>
{event_sections}
  <h3 class="section-title patch">🔧 PatchNote Posts</h3>
{patch_sections}
  <footer style="margin-top:40px;padding:20px 0 8px;text-align:center;color:#7f8c8d;font-size:12px;border-top:1px solid #e7eef6;">
    Generated with <a href="https://claude.ai/" target="_blank" style="color:#1a4d8f;text-decoration:none;font-weight:600;">Claude AI</a>
  </footer>
</main>

</div>
</body>
</html>
"""


def main() -> None:
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(render(), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(PROJ)}")


if __name__ == "__main__":
    main()
