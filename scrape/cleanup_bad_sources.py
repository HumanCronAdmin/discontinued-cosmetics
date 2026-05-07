"""
cleanup_bad_sources.py — Re-validate every reddit_mentions/sources URL by
fetching the post title and checking that the title contains BOTH the brand
AND a product keyword (>=4 chars). URLs that fail are removed.

Use after a scrape run with loose matching to remove false positives.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from _helpers import all_products, read_product, write_product

USER_AGENT = "discontinued-cosmetics/0.1 (cleanup; by humancronadmin)"


def fetch_title(reddit_url: str) -> str | None:
    api_url = reddit_url.rstrip("/") + ".json"
    req = urllib.request.Request(api_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        if isinstance(data, list) and data:
            children = data[0].get("data", {}).get("children", [])
            if children:
                return (children[0].get("data", {}).get("title") or "").lower()
    except Exception as e:
        print(f"  [WARN] fetch {reddit_url}: {e}")
    return None


def main() -> int:
    removed = 0
    kept = 0
    for path in all_products():
        fm, body = read_product(path)
        brand = (fm.get("brand") or "").lower()
        keys = [
            (fm.get("product_name") or "").lower(),
            (fm.get("slug") or "").replace("-", " ").lower(),
        ]
        keys = [k for k in keys if k and len(k) >= 4]
        if not brand:
            continue

        new_mentions = []
        for url in (fm.get("reddit_mentions") or []):
            if not isinstance(url, str) or "reddit.com" not in url:
                new_mentions.append(url)
                continue
            title = fetch_title(url)
            time.sleep(1)
            if title is None:
                new_mentions.append(url)  # keep on fetch failure
                continue
            if brand in title and any(k in title for k in keys):
                new_mentions.append(url)
                kept += 1
            else:
                safe_title = title[:80].encode("ascii", "replace").decode("ascii")
                print(f"  - {path.name}: drop {url} (title='{safe_title}')")
                removed += 1

        new_sources = [s for s in (fm.get("sources") or []) if s in new_mentions or "reddit.com" not in str(s)]
        # Above keeps non-reddit sources untouched and reddit sources only if also in new_mentions.

        changed = False
        if new_mentions != (fm.get("reddit_mentions") or []):
            fm["reddit_mentions"] = new_mentions
            changed = True
        if new_sources != (fm.get("sources") or []):
            fm["sources"] = new_sources
            changed = True
        if changed:
            write_product(path, fm, body)

    print(f"[OK] cleanup: removed={removed} kept={kept}")
    return removed


if __name__ == "__main__":
    main()
