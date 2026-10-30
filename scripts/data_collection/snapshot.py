"""Protection of the snapshots in data/ and comparison with a new export."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def ensure_outside_data_dir(output_file: Path) -> Path:
    """Refuses to write in data/: its files are the inputs pinned by SHA-256 in data/README.md."""
    output_file = Path(output_file).resolve()
    if DATA_DIR.resolve() in (output_file, *output_file.parents):
        raise ValueError(
            f"{output_file} is inside data/. A new export must not replace the snapshot "
            "used by the analysis: write it to outputs/data_collection/ and follow the "
            "steps in notebooks/00_data_collection.ipynb to adopt it."
        )
    return output_file


def compare_with_snapshot(new: pd.DataFrame, snapshot_file: Path, id_column: str) -> dict:
    """Counts the records kept, added and removed relative to the snapshot."""
    old = pd.read_csv(snapshot_file, encoding="utf-8-sig", dtype=str)
    new_ids, old_ids = set(new[id_column].astype(str)), set(old[id_column])
    return {
        "snapshot": Path(snapshot_file).name,
        "n_snapshot": len(old),
        "n_new_export": len(new),
        "same_columns": list(new.columns) == list(old.columns),
        "kept": len(new_ids & old_ids),
        "added": len(new_ids - old_ids),
        "removed": len(old_ids - new_ids),
    }
