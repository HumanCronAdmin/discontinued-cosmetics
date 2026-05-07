"""
import_seed_candidates.py — Convert data/seed_candidates.md table rows
into Astro content collection .md files. Skips rows whose product_name
or holy_grail_reason markers indicate EXCLUDED or NOTE-only entries.
All imported entries start as draft:true.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
SEED_FILE = ROOT / "data" / "seed_candidates.md"
PRODUCTS_DIR = ROOT / "src" / "src" / "content" / "products"


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80]


def yaml_str(v: str) -> str:
    if v is None or v == "" or v == "null":
        return "null"
    needs_quote = any(c in v for c in [":", "#", "'", '"', "[", "]", "{", "}", ","])
    if needs_quote:
        return '"' + v.replace('"', '\\"') + '"'
    return v


def parse_int_or_null(v: str):
    v = (v or "").strip()
    if not v or v.lower() == "null":
        return None
    m = re.search(r"\d{4}", v)
    if m:
        return int(m.group(0))
    return None


def parse_float_or_null(v: str):
    v = (v or "").strip()
    if not v or v.lower() == "null":
        return None
    m = re.search(r"\d+(\.\d+)?", v)
    if m:
        return float(m.group(0))
    return None


def main() -> int:
    text = SEED_FILE.read_text(encoding="utf-8")
    PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)

    imported = 0
    skipped = 0
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 8:
            continue
        if cells[0] in ("brand", "---") or cells[0].startswith("---"):
            continue

        brand, product_name, category, ly, dy, price, src, reason = cells[:8]
        # Skip header separator
        if all(c == "" or set(c) <= {"-", " "} for c in cells):
            continue
        # Skip excluded
        if "EXCLUDED" in reason.upper() or "EXCLUDED" in product_name.upper():
            skipped += 1
            continue
        if src.lower() in ("null", "", "none") or not src.startswith("http"):
            skipped += 1
            continue
        if "do not import" in reason.lower():
            skipped += 1
            continue

        # Validate category against schema enum
        cat = category.lower().strip()
        valid_cats = {"lipstick", "eyeshadow", "foundation", "blush", "mascara", "fragrance", "skincare"}
        if cat not in valid_cats:
            skipped += 1
            print(f"  [SKIP] {brand} {product_name}: invalid category '{cat}'")
            continue

        slug = slugify(f"{brand}-{product_name}")
        if not slug:
            skipped += 1
            continue

        path = PRODUCTS_DIR / f"{slug}.md"
        if path.exists():
            skipped += 1
            continue

        ly_int = parse_int_or_null(ly)
        dy_int = parse_int_or_null(dy)
        price_f = parse_float_or_null(price)

        fm_lines = [
            "---",
            f"brand: {yaml_str(brand)}",
            f"product_name: {yaml_str(product_name)}",
            f"slug: {slug}",
            f"category: {cat}",
            f"launched_year: {ly_int if ly_int is not None else 'null'}",
            f"discontinued_year: {dy_int if dy_int is not None else 'null'}",
            f"original_price_usd: {price_f if price_f is not None else 'null'}",
            "sold_history: []",
            "successor_product: null",
            "dupes: []",
            "reddit_mentions: []",
            f"sources:",
            f"  - {src}",
            "draft: true",
            "---",
            "",
        ]
        path.write_text("\n".join(fm_lines), encoding="utf-8")
        imported += 1
        print(f"  + {slug}")

    print(f"\n[OK] imported={imported} skipped={skipped}")
    return imported


if __name__ == "__main__":
    main()
