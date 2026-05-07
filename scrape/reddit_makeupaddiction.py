"""
reddit_makeupaddiction.py — PRAW search r/MakeupAddiction for discontinued
holy grail mentions, match against existing seed products, and append the
post URL to reddit_mentions[] and the comment thread URL to sources[].

Auth via vault keys: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
(or env vars). If absent, the script exits cleanly without writes.

Real data only. No invented mentions.
"""
from __future__ import annotations

import time
from _helpers import (
    secret, all_products, read_product, write_product, add_unique,
)

QUERIES = [
    "discontinued holy grail",
    "discontinued lipstick",
    "discontinued eyeshadow",
    "discontinued foundation",
    "bring back",
]
SUBREDDITS = ["MakeupAddiction", "MUAontheCheap", "PanPorn"]
PER_QUERY_LIMIT = 25


def main() -> int:
    cid = secret("REDDIT_CLIENT_ID")
    csec = secret("REDDIT_CLIENT_SECRET")
    ua = secret("REDDIT_USER_AGENT") or "discontinued-cosmetics/0.1 by humancronadmin"
    if not cid or not csec:
        print("[SKIP] REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET missing.")
        return 0

    try:
        import praw  # type: ignore
    except ImportError:
        print("[SKIP] praw not installed (pip install praw).")
        return 0

    reddit = praw.Reddit(client_id=cid, client_secret=csec, user_agent=ua)

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
            try:
                for post in reddit.subreddit(sub).search(q, limit=PER_QUERY_LIMIT, sort="relevance"):
                    text = (post.title + "\n" + (post.selftext or "")).lower()
                    url = f"https://reddit.com{post.permalink}"
                    for path, fm, body, brand, keys in products:
                        if brand and brand in text and any(k in text for k in keys):
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
            except Exception as e:
                msg = str(e)
                if "429" in msg or "403" in msg:
                    print(f"[STOP] Rate limited: {e}")
                    return updated
                print(f"  [WARN] {sub} '{q}': {e}")
    print(f"[OK] reddit_makeupaddiction updates: {updated}")
    return updated


if __name__ == "__main__":
    main()
