"""Export of the master table of the Águeda open data datasets (CKAN API).

Moved from data_collection/import_data_agueda.py. The 14 columns are those of
data/agueda_tabela_mae_datasets.csv, read by the notebooks in notebooks/agueda/.
The API is public: no key is needed. The extras keys in Portuguese
(e.g. "periodicidade", "categoria") are kept because they are names used by
the portal, not text of this module.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import requests

from .snapshot import ensure_outside_data_dir

BASE = "https://dadosabertos.cm-agueda.pt/pt_PT/api/3/action"
CATALOG_URL = "https://dadosabertos.cm-agueda.pt/pt_PT/dataset/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
    "Referer": CATALOG_URL,
}


def new_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def warmup(session):
    # "Warm up" the session: obtains cookies from the site
    r = session.get(CATALOG_URL, timeout=60)
    r.raise_for_status()


def ckan_get(session, action: str, params: dict | None = None, retries: int = 6) -> dict:
    url = f"{BASE}/{action}"
    params = params or {}

    for attempt in range(retries):
        r = session.get(url, params=params, timeout=60)

        if r.status_code == 403:
            # progressive backoff and a new warmup
            wait = min(2 ** attempt, 30)
            print(f"[403] Temporarily blocked. Waiting {wait}s and retrying...")
            time.sleep(wait)
            warmup(session)
            continue

        r.raise_for_status()
        data = r.json()
        if not data.get("success"):
            raise RuntimeError(data)
        return data["result"]

    raise RuntimeError(f"Failed after {retries} attempts (persistent 403) at {url}")


def extras_to_dict(extras):
    return {e.get("key"): e.get("value") for e in (extras or [])}


def pick_first(extras_dict, keys):
    for k in keys:
        v = extras_dict.get(k)
        if v not in (None, "", "null"):
            return v
    return None


def guess_update_frequency(extras_dict):
    return pick_first(extras_dict, [
        "update_frequency", "frequency", "accrual_periodicity", "dcat:accrualPeriodicity",
        "periodicity", "periodicidade", "frequencia_atualizacao",
        "Frequência", "Frequencia", "Frequência de atualização", "Frequencia de atualizacao",
    ])


def safe_join(items):
    items = [x for x in items if x not in (None, "", "null")]
    seen, uniq = set(), []
    for x in items:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return "; ".join(uniq)


def guess_theme(extras_dict, groups):
    # theme/category: prefer groups; if empty, try extras
    if groups:
        return safe_join(groups)
    return pick_first(extras_dict, ["theme", "dcat:theme", "categoria", "category", "tematica", "temática"])


def resources_json(resources):
    return json.dumps(
        [{"resource_id": r.get("id"), "name": r.get("name"), "format": r.get("format"), "url": r.get("url")}
         for r in (resources or [])],
        ensure_ascii=False
    )


def package_to_row(pkg) -> dict:
    """Converts one CKAN package into one row of the master table."""
    extras = extras_to_dict(pkg.get("extras"))
    tags = [t.get("name") for t in (pkg.get("tags") or [])]
    groups = [g.get("title") or g.get("name") for g in (pkg.get("groups") or [])]

    org = pkg.get("organization") or {}
    publisher = org.get("title") or org.get("name")

    res = pkg.get("resources") or []
    res_formats = [r.get("format") for r in res]
    res_urls = [r.get("url") for r in res]

    return {
        "id": pkg.get("id"),
        "name": pkg.get("name"),
        "title": pkg.get("title"),
        "description": pkg.get("notes"),
        "tags": safe_join(tags),
        "theme_category": guess_theme(extras, groups),
        "publisher_owner": publisher,
        "update_frequency": guess_update_frequency(extras),
        "resources_formats": safe_join(res_formats),
        "resources_urls": safe_join(res_urls),
        "metadata_created": pkg.get("metadata_created"),
        "metadata_modified": pkg.get("metadata_modified"),
        "license_id": pkg.get("license_id"),
        "resources_json": resources_json(res),
    }


def export_master_table(output_file: Path, page_size=25, pause=0.3) -> pd.DataFrame:
    """Exports all datasets of the portal to output_file (CSV, UTF-8 with BOM).

    page_size = 25: lower = less risk of being blocked (can be raised to 50/100).
    """
    output_file = ensure_outside_data_dir(output_file)
    session = new_session()
    warmup(session)

    rows = []
    start = 0
    while True:
        result = ckan_get(session, "package_search", {"q": "*:*", "rows": page_size, "start": start})
        packages = result.get("results", [])
        if not packages:
            break
        rows.extend(package_to_row(pkg) for pkg in packages)
        start += page_size
        time.sleep(pause)  # "gentle" on the server

    df = pd.DataFrame(rows)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    return df
