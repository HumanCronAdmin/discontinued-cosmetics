"""
reddit_makeupaddiction.py — Reddit public JSON endpoint search for
discontinued holy grail mentions in r/MakeupAddiction etc. No API key
required (matches existing pipeline pattern in
scripts/collect_niche_3indicators.py).

For each existing product, find posts whose title/selftext mention the
brand AND the product name; append post URL to reddit_mentions[] and
sources[].

Real data only. No invented mentions.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from _helpers import all_products, read_product, write_product, add_unique

QUERIES = [
    "discontinued holy grail",
    "discontinued lipstick",
    "discontinued eyeshadow",
    "discontinued foundation",
    "discontinued mascara",
    "discontinued blush",
    "discontinued fragrance",
    "bring back",
    "where can I find",
    "looking for",
    "miss this product",
    "old formula",
    "reformulated",
]
SUBREDDITS = [
    "MakeupAddiction", "MUAontheCheap", "PanPorn",
    "BeautyGuruChatter", "Sephora", "Ulta", "fragrance",
    "MakeupRehab", "AsianBeauty",
]
PER_QUERY_LIMIT = 25
USER_AGENT = "discontinued-cosmetics/0.1 (by humancronadmin)"


def fetch_reddit_search(subreddit: str, query: str, limit: int = 25):
    q = urllib.parse.quote(query)
    url = (
        f"https://www.reddit.com/r/{subreddit}/search.json"
        f"?q={q}&restrict_sr=1&sort=relevance&limit={limit}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("data", {}).get("children", [])
    except urllib.error.HTTPError as e:
        if e.code in (429, 403):
            print(f"  [STOP] Reddit HTTP {e.code} on r/{subreddit}")
            return None
        print(f"  [WARN] HTTP {e.code} on r/{subreddit} q='{query}'")
        return []
    except Exception as e:
        print(f"  [WARN] Fetch error r/{subreddit} q='{query}': {e}")
        return []


def main() -> int:
    products = []
    for p in all_products():
        fm, body = read_product(p)
        keys = [
            (fm.get("product_name") or "").lower(),
            (fm.get("slug") or "").replace("-", " ").lower(),
        ]
        brand = (fm.get("brand") or "").lower()
        products.append((p, fm, body, brand, [k for k in keys if k]))

    updated = 0
    for sub in SUBREDDITS:
        for q in QUERIES:
            children = fetch_reddit_search(sub, q, PER_QUERY_LIMIT)
            if children is None:
                return updated
            for ch in children:
                d = ch.get("data") or {}
                title = (d.get("title") or "").lower()
                selftext = (d.get("selftext") or "").lower()
                text = title + "\n" + selftext
                permalink = d.get("permalink") or ""
                if not permalink:
                    continue
                url = f"https://reddit.com{permalink}"
                for path, fm, body, brand, keys in products:
                    # Strict: title MUST contain both brand AND a product keyword (not selftext)
                    # Prevents false positives from unrelated posts that mention the brand in passing.
                    has_brand_title = brand and brand in title
                    has_key_title = any(k for k in keys if k and len(k) >= 4 and k in title)
                    if has_brand_title and has_key_title:
                        mentions = list(fm.get("reddit_mentions") or [])
                        srcs = list(fm.get("sources") or [])
                        changed = False
                        if add_unique(mentions, url):
                            fm["reddit_mentions"] = mentions
                            changed = True
                        if add_unique(srcs, url):
                            fm["sources"] = srcs
                            changed = True
                        if changed:
                            write_product(path, fm, body)
                            updated += 1
                            print(f"  + {path.name}: {url}")
            time.sleep(2)
    print(f"[OK] reddit_makeupaddiction updates: {updated}")
    return updated


if __name__ == "__main__":
    main()
