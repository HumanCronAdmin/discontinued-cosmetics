"""
gbnf_estee_lauder.py — Scrape Estee Lauder "Gone But Not Forgotten" archive
listing to confirm discontinued status / years for matching products.

The official URL has shifted historically; we accept any of:
  https://www.esteelauder.com/customer-service/gone-but-not-forgotten
  https://www.esteelauder.com/gbnf
Override with ESTEE_GBNF_URL env/vault. If the page is unreachable or no
matches found, the script exits without writes (no fabricated entries).
"""
from __future__ import annotations

import re
import urllib.request
from _helpers import secret, all_products, read_product, write_product, add_unique

DEFAULT_URL = "https://www.esteelauder.com/customer-service/gone-but-not-forgotten"


def _fetch(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[WARN] GBNF fetch: {e}")
        return None


def main() -> int:
    url = secret("ESTEE_GBNF_URL") or DEFAULT_URL
    html = _fetch(url)
    if not html:
        print("[SKIP] GBNF page unreachable.")
        return 0
    try:
        from bs4 import BeautifulSoup  # type: ignore
    except ImportError:
        print("[SKIP] beautifulsoup4 not installed.")
        return 0
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    updated = 0
    for path in all_products():
        fm, body = read_product(path)
        brand = (fm.get("brand") or "").lower()
        if "estee" not in brand and "estée" not in brand:
            continue
        name = (fm.get("product_name") or "").lower()
        if not name or name not in text:
            continue
        # Try to detect a 4-digit year next to the product name
        idx = text.find(name)
        window = text[max(0, idx - 80): idx + 200]
        m = re.search(r"discontinued[^0-9]{0,20}(19|20)\d{2}", window) or re.search(r"(19|20)\d{2}", window)
        srcs = list(fm.get("sources") or [])
        changed = False
        if add_unique(srcs, url):
            fm["sources"] = srcs
            changed = True
        if m and not fm.get("discontinued_year"):
            year = int(m.group(0)[-4:])
            fm["discontinued_year"] = year
            changed = True
        if changed:
            write_product(path, fm, body)
            updated += 1
            print(f"  + {path.name}: GBNF confirmed")
    print(f"[OK] gbnf_estee_lauder updates: {updated}")
    return updated


if __name__ == "__main__":
    main()
