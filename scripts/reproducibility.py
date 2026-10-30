"""Recording and minimal checking of the runs compared in the notebooks."""

from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path


PACKAGES = (
    "numpy", "pandas", "scipy", "scikit-learn", "torch", "sentence-transformers",
    "transformers", "tokenizers", "spacy", "pt_core_news_sm", "openpyxl",
    "matplotlib", "seaborn",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def hash_notebook_sources(path: Path) -> str:
    """Identifies the code and the narrative without depending on the saved outputs."""
    notebook = json.loads(Path(path).read_text(encoding="utf-8"))
    sources = [(cell["cell_type"], cell["source"]) for cell in notebook["cells"]]
    data_rows = json.dumps(sources, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data_rows).hexdigest()


def save_manifest(
    excel: Path, inputs: dict[str, Path], model_name: str, review: str,
    experiment_id: str, notebook: Path, limit: int, seed: int,
) -> Path:
    """Stores the identity of the data, model, code, environment and Excel file produced."""
    excel, notebook = Path(excel), Path(notebook)
    if not excel.is_file():
        raise FileNotFoundError(f"Excel file of the run missing: {excel}")
    for name_, file_path in inputs.items():
        if not Path(file_path).is_file():
            raise FileNotFoundError(f"Input {name_} missing: {file_path}")
    document = {
        "experiment": experiment_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "inputs_sha256": {name_: sha256(file_path) for name_, file_path in inputs.items()},
        "excel_sha256": sha256(excel),
        "notebook_sources_sha256": hash_notebook_sources(notebook),
        "helper_sha256": sha256(Path(__file__)),
        "model": model_name,
        "model_revision": review,
        "max_seq_length": int(limit),
        "seed": int(seed),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {name_: metadata.version(name_) for name_ in PACKAGES},
    }
    destination = excel.parent / "run_manifest.json"
    destination.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destination


def validate_comparison(
    previous: Path, current_run: Path, previous_experiment: str, current_experiment: str,
) -> None:
    """Rejects missing or old files, or files generated with different data/model."""
    manifests = []
    for excel, experiment_id in ((Path(previous), previous_experiment),
                               (Path(current_run), current_experiment)):
        file_path = excel.parent / "run_manifest.json"
        if not excel.is_file() or not file_path.is_file():
            raise FileNotFoundError(
                f"The comparison requires {excel} and {file_path}. Run the notebooks first in the order given in the README."
            )
        doc = json.loads(file_path.read_text(encoding="utf-8"))
        if doc["experiment"] != experiment_id or doc["excel_sha256"] != sha256(excel):
            raise ValueError(f"Old result or incompatible experiment: {excel}")
        manifests.append(doc)
    a, b = manifests
    for field in ("inputs_sha256", "model", "model_revision", "seed", "python", "platform", "packages"):
        if a[field] != b[field]:
            raise ValueError(f"Comparison not valid: '{field}' differs between the runs")
