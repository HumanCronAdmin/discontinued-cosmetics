"""
run_all.py — Run every scraper sequentially. Each scraper auto-skips when
its credentials are absent so this can run safely on dev machines.

After all scrapers finish, products with sources >= MIN_SOURCES are
flipped to draft:false automatically (handled inside write_product).
"""
from __future__ import annotations

import sys
import traceback


def _run(name: str):
    print(f"\n=== {name} ===")
    try:
        mod = __import__(name)
        mod.main()
    except SystemExit:
        raise
    except Exception:
        print(f"[ERR] {name} failed:")
        traceback.print_exc()


def main() -> None:
    sys.path.insert(0, ".")
    for name in (
        "reddit_makeupaddiction",
        "ebay_sold",
        "gbnf_estee_lauder",
        "temptalia_archive",
    ):
        _run(name)


if __name__ == "__main__":
    main()
