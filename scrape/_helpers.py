"""
_helpers.py — Shared helpers for discontinued-cosmetics scrapers.

Loads secrets via Claude-Workspace/scripts/vault.py (get_secret) and falls back
to os.environ. Provides product .md frontmatter read/write utilities so all
scrapers append data and never overwrite seed fields.

NEVER hardcode API keys here. Vault first, env second.
"""
from __future__ import annotations

import os
import sys
import re
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = PROJECT_ROOT / "src" / "src" / "content" / "products"
WORKSPACE_ROOT = PROJECT_ROOT.parent.parent
SCRIPTS_DIR = WORKSPACE_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from vault import get_secret as _vault_get  # type: ignore
except Exception:  # pragma: no cover
    _vault_get = None  # type: ignore


MIN_SOURCES = 3  # spec.md: data_min_sources = 3


def secret(key: str) -> str | None:
    """Vault first, env var fallback. Never returns hardcoded values."""
    if _vault_get is not None:
        try:
            v = _vault_get(key)
            if v:
                return v
        except Exception:
            pass
    return os.environ.get(key)


_FM_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def read_product(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    m = _FM_RE.match(text)
    if not m:
        raise ValueError(f"No frontmatter: {path}")
    fm = yaml.safe_load(m.group(1)) or {}
    return fm, m.group(2)


def write_product(path: Path, fm: dict[str, Any], body: str) -> None:
    # Auto-flip draft:false when sources >= MIN_SOURCES
    sources = fm.get("sources") or []
    if isinstance(sources, list) and len(sources) >= MIN_SOURCES:
        fm["draft"] = False
    out = "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip() + "\n---\n" + body
    path.write_text(out, encoding="utf-8")


def all_products() -> list[Path]:
    return sorted(PRODUCTS_DIR.glob("*.md"))


def add_unique(lst: list, item: Any) -> bool:
    if item in lst:
        return False
    lst.append(item)
    return True
