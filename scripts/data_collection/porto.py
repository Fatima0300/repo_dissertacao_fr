"""Export of the master table of the Porto datasets (CKAN API).

Moved from data_collection/data_import_porto.ipynb. The 18 columns are those of
data/porto_tabela_mae_datasets.csv, read by the notebooks in notebooks/porto/.
The API is public: no key is needed.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from .snapshot import ensure_outside_data_dir

CKAN_API_URL = "https://opendata.porto.digital/api/3/action/package_search"
DATASET_URL = "https://opendata.porto.digital/dataset/"
SOURCE_PORTAL = "Portal de Dados Abertos do Porto"


def fetch_all_ckan_datasets(api_url=CKAN_API_URL, rows_per_page=100, timeout=30):
    """Reads all pages of package_search and returns the list of datasets."""
    all_datasets = []
    start = 0
    total = None

    while total is None or start < total:
        params = {
            "start": start,
            "rows": rows_per_page
        }

        response = requests.get(
            api_url,
            params=params,
            timeout=timeout
        )
        response.raise_for_status()

        data = response.json()

        if not data.get("success", False):
            raise RuntimeError("The API responded, but returned success=False.")

        result = data["result"]
        total = result["count"]
        batch = result["results"]

        all_datasets.extend(batch)

        print(f"Extracted {len(all_datasets)} of {total} datasets...")

        start += rows_per_page

    return all_datasets


def normalize_ckan_dataset(dataset, exported_at):
    """Converts one CKAN dataset into one row of the master table."""
    resources = dataset.get("resources", []) or []
    organization = dataset.get("organization") or {}

    tags = [
        tag.get("name")
        for tag in dataset.get("tags", [])
        if tag.get("name")
    ]

    groups = [
        group.get("display_name") or group.get("name")
        for group in dataset.get("groups", [])
        if group.get("display_name") or group.get("name")
    ]

    resource_formats = sorted({
        str(resource.get("format", "")).strip()
        for resource in resources
        if resource.get("format")
    })

    resource_names = [
        resource.get("name")
        for resource in resources
        if resource.get("name")
    ]

    resource_urls = [
        resource.get("url")
        for resource in resources
        if resource.get("url")
    ]

    resource_ids = [
        resource.get("id")
        for resource in resources
        if resource.get("id")
    ]

    return {
        "dataset_id": dataset.get("id"),
        "name": dataset.get("name"),
        "title": dataset.get("title"),
        "description": dataset.get("notes"),
        "organization": organization.get("title") or organization.get("name"),
        "groups": "; ".join(groups),
        "tags": "; ".join(tags),
        "license": dataset.get("license_title") or dataset.get("license_id"),
        "metadata_created": dataset.get("metadata_created"),
        "metadata_modified": dataset.get("metadata_modified"),
        "num_resources": len(resources),
        "resource_ids": "; ".join(resource_ids),
        "resource_names": "; ".join(resource_names),
        "resource_formats": "; ".join(resource_formats),
        "resource_urls": "; ".join(resource_urls),
        "dataset_url": f"{DATASET_URL}{dataset.get('name')}",
        "source_portal": SOURCE_PORTAL,
        "exported_at": exported_at,
    }


def export_master_table(output_file: Path, rows_per_page=100, timeout=30) -> pd.DataFrame:
    """Exports all datasets of the portal to output_file (CSV, UTF-8 with BOM).

    `exported_at` is taken once, at the start, so that every row of the
    export carries the same timestamp.
    """
    output_file = ensure_outside_data_dir(output_file)
    exported_at = datetime.now().isoformat(timespec="seconds")

    datasets_raw = fetch_all_ckan_datasets(
        rows_per_page=rows_per_page,
        timeout=timeout
    )
    df_porto = pd.DataFrame(
        [normalize_ckan_dataset(dataset, exported_at) for dataset in datasets_raw]
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_porto.to_csv(output_file, index=False, encoding="utf-8-sig")
    return df_porto
