"""
temptalia_archive.py — Search Temptalia's archived review pages to fill
launched_year / category for products that lack them. Uses the public
search URL (no auth). Conservative: only updates fields that are empty.
"""
from __future__ import annotations

import re
import urllib.parse
import urllib.request
from _helpers import secret, all_products, read_product, write_product, add_unique

SEARCH_URL = "https://www.temptalia.com/?s={q}"


def _fetch(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[WARN] Temptalia fetch: {e}")
        return None


def main() -> int:
    try:
        from bs4 import BeautifulSoup  # type: ignore
    except ImportError:
        print("[SKIP] beautifulsoup4 not installed.")
        return 0

    updated = 0
    for path in all_products():
        fm, body = read_product(path)
        q = f"{fm.get('brand','')} {fm.get('product_name','')}".strip()
        if not q:
            continue
        url = SEARCH_URL.format(q=urllib.parse.quote_plus(q))
        html = _fetch(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        first = soup.select_one("article a[href]")
        if not first:
            continue
        href = first.get("href")
        if not href:
            continue
        srcs = list(fm.get("sources") or [])
        changed = False
        if add_unique(srcs, href):
            fm["sources"] = srcs
            changed = True
        # detect year from review page
        if not fm.get("launched_year"):
            review = _fetch(href)
            if review:
                m = re.search(r"(launched|released|introduced)[^0-9]{0,15}(19|20)\d{2}", review.lower())
                if m:
                    fm["launched_year"] = int(m.group(0)[-4:])
                    changed = True
        if changed:
            write_product(path, fm, body)
            updated += 1
            print(f"  + {path.name}: temptalia {href}")
    print(f"[OK] temptalia_archive updates: {updated}")
    return updated


if __name__ == "__main__":
    main()
