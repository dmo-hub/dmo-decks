"""Generate docs/digimon.html from scan_result_digimon.json.

Re-run after scan_digimon.py to refresh the published Digimon report.
"""

import json
import re
import sys
import urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROJ = Path(__file__).resolve().parent.parent
SRC = PROJ / "data" / "scan_result_digimon.json"
KR_INDEX = PROJ / "data" / "kr_news_index.json"
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


def _link_text(url: str, kind: str) -> str:
    """Short, readable text for a source link.
    TH URLs have long URL-encoded Thai slugs — collapse to just the trailing
    `patch-N` if present, else decode the slug to Thai text."""
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    if kind == "th":
        # If slug ends with `-NUMBER`, show just that (e.g., "patch-87")
        m = re.search(r"(patch|รายละเอียดการอัพเดท)?-?(\d+)$", urllib.parse.unquote(slug))
        if m and m.group(2):
            return f"patch -{m.group(2)}"
        # Fall back to decoded Thai slug
        return urllib.parse.unquote(slug)
    return slug


def canonical_src_key(url: str) -> tuple[str, str]:
    """Canonical (kind, id) per source URL, so two URLs pointing to the same
    post (different query-string order) dedupe correctly."""
    if "digimonmasters.com" in url:
        m = re.search(r"[?&]o=(\d+)", url)
        return ("kr", m.group(1) if m else url)
    if "gameking.com" in url:
        m = re.search(r"[?&]idx=(\d+)", url)
        return ("na", m.group(1) if m else url)
    if "vplay.in.th" in url:
        return ("th", url.rstrip("/").rsplit("/", 1)[-1])
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

  /* Post card */
  .post { background: white; border-radius: 10px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
  .post-header { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; margin-bottom: 4px; }
  .post-header .idx-badge { background: #1a4d8f; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
  .post-header h2 { color: #2c3e50; font-size: 19px; margin: 0; }
  .post-header .date { color: #95a5a6; font-size: 13px; }
  .src { font-size: 12px; margin: 0 0 16px 0; display: flex; flex-wrap: wrap; gap: 6px 14px; align-items: center; }
  .src a { color: #2c6fb8; text-decoration: none; }
  .src a:hover { text-decoration: underline; }
  .src .src-label { color: #95a5a6; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
  .src .src-date { color: #95a5a6; font-size: 11px; margin: 0 4px; }
  .src .src-kr a { color: #c0392b; }
  .src .src-th a { color: #1f8c4d; }

  /* Digimon list — orange-border cards matching deck style */
  .digimon-list { list-style: none; padding: 0; margin: 8px 0 0 0; display: grid; gap: 10px; }
  .digimon-list li { padding: 12px 18px; background: #fafbfc; border-radius: 8px; box-shadow: 0 0 0 2px #f39c12;
                     font-size: 16px; font-weight: 700; color: #1a4d8f; }
  .digimon-name { display: block; margin-bottom: 6px; }

  /* Attribute chips — one row per category (Attribute / Element / Families)
     with a left-aligned label so icons line up across rows. */
  .chips-row { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; align-items: center;
               font-size: 12px; color: #7f8c8d; }
  .chips-row .chips-label { font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
                            font-size: 10.5px; color: #95a5a6; min-width: 76px; }
  .chip-icon-only { width: 28px; height: 28px; object-fit: contain; cursor: help;
                    transition: transform 0.12s ease; }
  .chip-icon-only:hover { transform: scale(1.18); }
  .rebalance-src { margin-left: 8px; font-size: 10.5px; color: #2c6fb8;
                   text-decoration: none; padding: 2px 6px; border-radius: 4px;
                   background: #eef4fb; font-weight: 500; }
  .rebalance-src:hover { background: #d8e6f5; text-decoration: underline; }

  /* Filter bar at top of report — repurposes the old text+pill chip look */
  .filter-bar { background: white; border-radius: 10px; padding: 14px 18px; margin-bottom: 18px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
  .filter-bar h4 { margin: 0 0 6px 0; font-size: 11px; color: #888;
                   text-transform: uppercase; letter-spacing: 0.6px; }
  .filter-group { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; align-items: center; }
  .filter-group:last-child { margin-bottom: 0; }
  .filter-pill { padding: 4px 11px 4px 6px; border-radius: 999px; font-size: 12px;
                 font-weight: 500; letter-spacing: 0.3px; border: 1px solid transparent;
                 display: inline-flex; align-items: center; gap: 5px; cursor: pointer;
                 user-select: none; opacity: 0.55; transition: opacity 0.12s, transform 0.12s; }
  .filter-pill:hover { opacity: 1; }
  .filter-pill.active { opacity: 1; transform: scale(1.04);
                        box-shadow: 0 0 0 2px rgba(26,77,143,0.35); }
  .filter-pill img { width: 18px; height: 18px; object-fit: contain; flex-shrink: 0; }
  .filter-reset { background: transparent; color: #2c6fb8; border: none; padding: 4px 8px;
                  font-size: 11px; cursor: pointer; text-decoration: underline; }
  .filter-count { font-size: 11px; color: #95a5a6; margin-left: auto; }
  /* Basic attribute colors */
  .filter-pill.chip-attr-VA { background: #d6f0d6; color: #1f6b1f; }
  .filter-pill.chip-attr-VI { background: #efd9ef; color: #6b1f6b; }
  .filter-pill.chip-attr-DA { background: #d6e3f5; color: #1a4d8f; }
  .filter-pill.chip-attr-FR { background: #f0e4cc; color: #8a6a1a; }
  .filter-pill.chip-attr-UN { background: #ebebeb; color: #555; }
  .filter-pill.chip-elem { background: #eef2f5; color: #2c3e50; border-color: #d4dce3; }
  .filter-pill.chip-families { background: #fff1d6; color: #9b6e1a; border-color: #f1d49a; }

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


def elem_slug(value: str) -> str:
    return ELEM_ICON.get(value, value.replace(" ", "_"))


def family_slug(value: str) -> str:
    return FAMILY_ICON.get(value, value.replace(" ", "_"))


def render_digimon(name: str, attrs: dict | None, show_name: bool = True) -> str:
    """Render a digimon's attribute icons in two rows:
      row 1 — basic attribute + natural attribute (icon only, no text)
      row 2 — families (icon only, no text)
    Icon files: docs/img/icons/<category>-<slug>.png. Hover/title shows the
    full canonical name. Coloured text-pill versions of these chips now live
    in the filter bar at the top of the report.
    """
    rows: list[str] = []
    if attrs:
        if attrs.get("attribute"):
            v = attrs["attribute"]
            rows.append(
                f'<div class="chips-row">'
                f'<span class="chips-label">Attribute</span>'
                f'<img class="chip-icon-only" src="img/icons/attr-{v}.png" '
                f'alt="{v}" title="{v}"></div>'
            )
        if attrs.get("natural_attribute"):
            v = attrs["natural_attribute"]
            rows.append(
                f'<div class="chips-row">'
                f'<span class="chips-label">Element</span>'
                f'<img class="chip-icon-only" src="img/icons/elem-{elem_slug(v)}.png" '
                f'alt="{v}" title="{v}"></div>'
            )
        if attrs.get("families"):
            fam_icons = "".join(
                f'<img class="chip-icon-only" src="img/icons/field-{family_slug(f)}.png" '
                f'alt="{f}" title="{f}">'
                for f in attrs["families"]
            )
            # Append small "updated by [eXXX]" links for any post-release
            # rebalance that contributed to this digimon's family list.
            src_links = "".join(
                f'<a class="rebalance-src" href="{s["url"]}" target="_blank" '
                f'title="Families updated in {s["kind"]}_{s["idx"]}">'
                f'updated&nbsp;{s["kind"][0]}{s["idx"]}</a>'
                for s in attrs.get("rebalance_sources", [])
            )
            rows.append(
                f'<div class="chips-row">'
                f'<span class="chips-label">Families</span>{fam_icons}{src_links}</div>'
            )

    chip_block = "".join(rows)
    name_html = f'<span class="digimon-name">{name}</span>' if show_name else ""
    return f"{name_html}{chip_block}" or "&nbsp;"


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

    def _sort_key(item: tuple[str, str, dict]) -> tuple[str, int]:
        """Sort posts chronologically by gameking date (MM-DD-YYYY → YYYYMMDD).
        Tie-break by idx so order is stable within a single day."""
        _kind, idx, p = item
        d = p.get("date") or "00-00-0000"
        mm, dd, yyyy = d.split("-")
        return (f"{yyyy}{mm}{dd}", int(idx))

    # Merge events + patches into a single chronological list.
    # Anchor prefix `e`/`p` is kept so old deep-links keep working and the
    # filter JS can still distinguish them via data-* if ever needed.
    merged = sorted(
        [("event", idx, p) for idx, p in events.items()]
        + [("patch", idx, p) for idx, p in patches.items()],
        key=_sort_key,
    )

    # TOC: single chronological list — no more EventView/PatchNote split.
    toc_links = "\n  ".join(
        f'<a href="#{("e" if kind == "event" else "p")}{idx}">idx {idx} — '
        f'{", ".join(p["digimon"])[:50]}'
        f'{"..." if len(", ".join(p["digimon"])) > 50 else ""}</a>'
        for kind, idx, p in merged
    )

    def render_post(idx: str, p: dict, kind: str) -> str:
        prefix = "e" if kind == "event" else "p"
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
        # Image priority: TH > NA > KR (user prefers Thai-server banner when available).
        img_path = p.get("image_th") or p.get("image") or p.get("image_kr")
        img_block = (
            f'<a href="{img_path}" target="_blank">'
            f'<img class="post-image" src="{img_path}" alt="idx {idx}" loading="lazy">'
            f'</a>\n    '
            if img_path else ""
        )
        def src_span(url: str) -> str:
            kind, oid = canonical_src_key(url)
            cls = {"kr": "src-kr", "th": "src-th", "na": "src-en"}.get(kind, "src-en")
            label = {"kr": "KR", "th": "TH", "na": "NA"}.get(kind, "?")
            if kind == "kr":
                date_str = fmt_iso_date(kr_dates.get(oid))
            elif kind == "th":
                date_str = fmt_iso_date(p.get("date_th"))
            else:
                date_str = fmt_date(p["date"])
            return (
                f'<span class="{cls}"><span class="src-label">{label}</span>'
                f'<span class="src-date">{date_str}</span>'
                f'<a href="{url}" target="_blank">{_link_text(url, kind)} ↗</a></span>'
            )

        # Dedupe by canonical key — two URLs pointing to the same post but
        # with different query-string ordering should collapse to one entry.
        # Order: NA, KR, TH (renders left-to-right in that order).
        seen: set[tuple[str, str]] = set()
        src_parts: list[str] = []
        for u in (p["source"], p.get("source_kr"), p.get("source_th")):
            if not u:
                continue
            key = canonical_src_key(u)
            if key in seen:
                continue
            seen.add(key)
            src_parts.append(src_span(u))
        src_html = "".join(src_parts)
        # Per-section data attributes so the filter JS can hide non-matching
        # posts without re-rendering. Comma-separated lists for multi-digimon
        # posts so a partial match (any digimon matches) keeps the section.
        all_attrs = sorted({a.get("attribute") for a in attrs_map.values() if a.get("attribute")})
        all_elems = sorted({a.get("natural_attribute") for a in attrs_map.values() if a.get("natural_attribute")})
        all_fams = sorted({f for a in attrs_map.values() for f in a.get("families", [])})
        data_attrs = (
            f'data-attr="{",".join(all_attrs)}" '
            f'data-elem="{",".join(all_elems)}" '
            f'data-family="{",".join(all_fams)}"'
        )
        return f"""  <section class="post" id="{prefix}{idx}" {data_attrs}>
    <div class="post-header">
      <span class="idx-badge">idx {idx}</span>
      <h2>{h2_text}</h2>
    </div>
    <p class="src">{src_html}</p>
    {img_block}<ul class="digimon-list">
      {items}
    </ul>
  </section>
"""

    all_sections = "\n".join(render_post(idx, p, kind) for kind, idx, p in merged)

    # Collect unique attribute/element/family values seen across all posts
    # for the filter bar. Order: deterministic for chip groups.
    all_posts = list(events.values()) + list(patches.values())
    seen_attrs: list[str] = []
    seen_elems: list[str] = []
    seen_fams: list[str] = []
    for p in all_posts:
        for a in p.get("attributes", {}).values():
            if a.get("attribute") and a["attribute"] not in seen_attrs:
                seen_attrs.append(a["attribute"])
            if a.get("natural_attribute") and a["natural_attribute"] not in seen_elems:
                seen_elems.append(a["natural_attribute"])
            for f in a.get("families", []):
                if f not in seen_fams:
                    seen_fams.append(f)
    # Sort with a friendly order for the basic-attribute row.
    attr_order = ["Vaccine", "Virus", "Data", "Free", "Unknown"]
    seen_attrs.sort(key=lambda x: (attr_order.index(x) if x in attr_order else 999, x))
    seen_elems.sort()
    seen_fams.sort()

    def filter_pill(category: str, value: str, slug: str, cls: str, icon_dir: str) -> str:
        return (
            f'<button class="filter-pill {cls}" '
            f'data-filter="{category}" data-value="{value}">'
            f'<img src="img/icons/{icon_dir}-{slug}.png" alt="">{value}</button>'
        )

    attr_pills = "".join(
        filter_pill("attr", v, v, f"chip-attr-{ATTR_ABBR_MAP.get(v, 'UN')}", "attr")
        for v in seen_attrs
    )
    elem_pills = "".join(
        filter_pill("elem", v, elem_slug(v), "chip-elem", "elem")
        for v in seen_elems
    )
    fam_pills = "".join(
        filter_pill("family", v, family_slug(v), "chip-families", "field")
        for v in seen_fams
    )

    filter_bar = f"""  <div class="filter-bar">
    <h4>Basic Attribute</h4>
    <div class="filter-group">{attr_pills}</div>
    <h4>Natural Attribute</h4>
    <div class="filter-group">{elem_pills}</div>
    <h4>Families <span style="font-weight:400;text-transform:none;color:#aaa;font-size:10px;">(เลือกได้หลายอัน — match ทุกอัน)</span></h4>
    <div class="filter-group">{fam_pills}<button class="filter-reset" id="filter-reset">reset</button><span class="filter-count" id="filter-count"></span></div>
  </div>"""

    filter_js = """
<script>
(() => {
  // attr/elem are single-select (radio); family is multi-select.
  // A post matches family when its families contain EVERY selected one (AND).
  const state = {attr: null, elem: null, family: new Set()};
  const pills = document.querySelectorAll('.filter-pill');
  const posts = document.querySelectorAll('section.post');
  const countEl = document.getElementById('filter-count');

  function apply() {
    let visible = 0;
    posts.forEach(s => {
      const a = (s.dataset.attr   || '').split(',');
      const e = (s.dataset.elem   || '').split(',');
      const f = (s.dataset.family || '').split(',');
      let show = true;
      if (state.attr && !a.includes(state.attr)) show = false;
      if (state.elem && !e.includes(state.elem)) show = false;
      if (state.family.size) {
        for (const wanted of state.family) {
          if (!f.includes(wanted)) { show = false; break; }
        }
      }
      s.style.display = show ? '' : 'none';
      if (show) visible++;
    });
    const active = [
      state.attr, state.elem, ...state.family
    ].filter(Boolean);
    countEl.textContent = active.length
      ? `${visible} โพสต์ ตรงตาม ${active.join(' + ')}`
      : '';
  }

  pills.forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.dataset.filter;
      const val = btn.dataset.value;
      if (key === 'family') {
        // multi-select: toggle membership
        if (state.family.has(val)) {
          state.family.delete(val);
          btn.classList.remove('active');
        } else {
          state.family.add(val);
          btn.classList.add('active');
        }
      } else {
        // single-select: same value clears; new value replaces
        if (state[key] === val) {
          state[key] = null;
          btn.classList.remove('active');
        } else {
          document.querySelectorAll(`.filter-pill[data-filter="${key}"]`)
            .forEach(b => b.classList.remove('active'));
          state[key] = val;
          btn.classList.add('active');
        }
      }
      apply();
    });
  });

  document.getElementById('filter-reset').addEventListener('click', () => {
    state.attr = null;
    state.elem = null;
    state.family.clear();
    pills.forEach(b => b.classList.remove('active'));
    apply();
  });
})();
</script>"""

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
  <h3>สารบัญ ({total_posts} โพสต์)</h3>
  {toc_links}
</aside>

<main>
  <div class="hero">
    <h1>DMO – Digimon Report</h1>
    <div class="hero-stats">
      <div class="hero-stat"><div class="num">{total_posts}</div><div class="lbl">โพสต์</div></div>
      <div class="hero-stat"><div class="num">{total_digimon}</div><div class="lbl">digimon ใหม่</div></div>
    </div>
  </div>

{filter_bar}

{all_sections}
  <footer style="margin-top:40px;padding:20px 0 8px;text-align:center;color:#7f8c8d;font-size:12px;border-top:1px solid #e7eef6;">
    Generated with <a href="https://claude.ai/" target="_blank" style="color:#1a4d8f;text-decoration:none;font-weight:600;">Claude AI</a>
  </footer>
</main>
{filter_js}

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
