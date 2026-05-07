# scrape/ — discontinued-cosmetics data pipeline

Fills `src/src/content/products/*.md` frontmatter with verified, real data.
No fabricated entries. Each scraper exits cleanly when its credentials are
missing (no error, no writes).

## Required environment / vault keys

| Key | Used by | Required? |
|---|---|---|
| `REDDIT_CLIENT_ID` | reddit_makeupaddiction.py | yes for Reddit step |
| `REDDIT_CLIENT_SECRET` | reddit_makeupaddiction.py | yes for Reddit step |
| `REDDIT_USER_AGENT` | reddit_makeupaddiction.py | optional (default: discontinued-cosmetics/0.1) |
| `EBAY_APP_ID` | ebay_sold.py | yes for eBay step |
| `EBAY_CERT_ID` | ebay_sold.py | yes for eBay step |
| `EBAY_OAUTH_TOKEN` | ebay_sold.py | optional (skips token fetch if set) |
| `EBAY_MARKETPLACE_INSIGHTS_TOKEN` | ebay_sold.py | optional (enables real sold listings) |
| `ESTEE_GBNF_URL` | gbnf_estee_lauder.py | optional override |

Secrets are read via `Claude-Workspace/scripts/vault.py:get_secret(key)`.
`os.environ` is the fallback. Never hardcode keys here.

## Install

```bash
pip install praw beautifulsoup4 pyyaml
```

## Run

```bash
# from projects/discontinued-cosmetics/scrape/
python run_all.py            # all scrapers
python reddit_makeupaddiction.py
python ebay_sold.py
python gbnf_estee_lauder.py
python temptalia_archive.py
```

## Auto-publish rule

A product whose `sources[]` reaches >= 3 unique URLs is auto-flipped to
`draft: false` by `_helpers.write_product`. Below the threshold the entry
stays drafted and Astro `getCollection` filters it out of the public site.
