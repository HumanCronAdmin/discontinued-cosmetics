"""
ebay_sold.py — Query eBay Browse API for each product and append the most
recent live listings to sold_history[]. NOTE: the public Browse API returns
active listings, not sold ones; sold-listing data requires Marketplace
Insights API approval. We use Browse listings as a price-floor proxy and tag
platform='ebay_active'. When EBAY_MARKETPLACE_INSIGHTS_TOKEN is present we
prefer that endpoint and tag platform='ebay_sold'.

Auth: requires EBAY_APP_ID + EBAY_CERT_ID (or pre-fetched EBAY_OAUTH_TOKEN)
in vault or env. If absent, exits cleanly.
"""
from __future__ import annotations

import base64
import datetime as dt
import json
import urllib.parse
import urllib.request
from _helpers import (
    secret, all_products, read_product, write_product, add_unique,
)

BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
INSIGHTS_URL = "https://api.ebay.com/buy/marketplace_insights/v1_beta/item_sales/search"
TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SCOPE_BROWSE = "https://api.ebay.com/oauth/api_scope"
LIMIT = 10


def _fetch_token() -> str | None:
    pre = secret("EBAY_OAUTH_TOKEN")
    if pre:
        return pre
    app_id = secret("EBAY_APP_ID")
    cert = secret("EBAY_CERT_ID")
    if not app_id or not cert:
        return None
    creds = base64.b64encode(f"{app_id}:{cert}".encode()).decode()
    body = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "scope": SCOPE_BROWSE,
    }).encode()
    req = urllib.request.Request(
        TOKEN_URL, data=body,
        headers={"Authorization": f"Basic {creds}",
                 "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())["access_token"]
    except Exception as e:
        print(f"[ERR] eBay token: {e}")
        return None


def _query(token: str, q: str, insights: bool) -> list[dict]:
    url = INSIGHTS_URL if insights else BROWSE_URL
    full = f"{url}?{urllib.parse.urlencode({'q': q, 'limit': LIMIT})}"
    req = urllib.request.Request(full, headers={
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
            return data.get("itemSales") or data.get("itemSummaries") or []
    except Exception as e:
        print(f"  [WARN] eBay '{q}': {e}")
        return []


def main() -> int:
    token = _fetch_token()
    if not token:
        print("[SKIP] eBay credentials missing (EBAY_APP_ID/EBAY_CERT_ID or EBAY_OAUTH_TOKEN).")
        return 0
    insights = bool(secret("EBAY_MARKETPLACE_INSIGHTS_TOKEN"))
    platform = "ebay_sold" if insights else "ebay_active"
    today = dt.date.today().isoformat()

    updated = 0
    for path in all_products():
        fm, body = read_product(path)
        q = f"{fm.get('brand','')} {fm.get('product_name','')}".strip()
        if not q:
            continue
        items = _query(token, q, insights)
        history = list(fm.get("sold_history") or [])
        srcs = list(fm.get("sources") or [])
        changed = False
        for it in items[:LIMIT]:
            price_obj = it.get("price") or it.get("lastSoldPrice") or {}
            try:
                price = float(price_obj.get("value"))
            except (TypeError, ValueError):
                continue
            url = it.get("itemWebUrl") or it.get("itemHref")
            if not url:
                continue
            entry = {"date": today, "platform": platform, "price_usd": price, "url": url}
            if add_unique(history, entry):
                changed = True
            add_unique(srcs, url)
        if changed:
            fm["sold_history"] = history
            fm["sources"] = srcs
            write_product(path, fm, body)
            updated += 1
            print(f"  + {path.name}: +{len(items)} listings")
    print(f"[OK] ebay_sold updates: {updated}")
    return updated


if __name__ == "__main__":
    main()
