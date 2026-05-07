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
WAYBACK_API = "https://archive.org/wayback/available?url={url}"
WAYBACK_LATEST = "https://web.archive.org/web/{ts}/{url}"


BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def _fetch(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers=BROWSER_HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[WARN] GBNF fetch: {e}")
        return None


def _fetch_via_wayback(target_url: str) -> tuple[str | None, str | None]:
    """Get latest Wayback snapshot of target URL. Returns (html, snapshot_url)."""
    import json
    try:
        api = WAYBACK_API.format(url=urllib.parse.quote(target_url, safe=""))
        req = urllib.request.Request(api, headers=BROWSER_HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        snap = data.get("archived_snapshots", {}).get("closest", {})
        if not snap.get("available"):
            return None, None
        snap_url = snap.get("url")
        if not snap_url:
            return None, None
        req2 = urllib.request.Request(snap_url, headers=BROWSER_HEADERS)
        with urllib.request.urlopen(req2, timeout=30) as r:
            return r.read().decode("utf-8", errors="ignore"), snap_url
    except Exception as e:
        print(f"[WARN] Wayback fetch: {e}")
        return None, None


def main() -> int:
    url = secret("ESTEE_GBNF_URL") or DEFAULT_URL
    html = _fetch(url)
    source_url = url
    if not html:
        print("[INFO] direct GBNF blocked. Trying Wayback Machine...")
        html, snap_url = _fetch_via_wayback(url)
        if html and snap_url:
            source_url = snap_url
            print(f"[OK] Wayback snapshot: {snap_url}")
    if not html:
        print("[SKIP] GBNF page unreachable (direct + wayback).")
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
        if add_unique(srcs, source_url):
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
