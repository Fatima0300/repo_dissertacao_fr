"""Checks the artefacts produced by scripts/reproduce.py."""

import json
from pathlib import Path

import nbformat
import pandas as pd

from reproduce import ROOT, NOTEBOOKS, AGUEDA_NOTEBOOKS

import sys
sys.path.insert(0, str(ROOT))
from scripts.reproducibility import hash_notebook_sources, sha256, validate_comparison


def check_city(city: str, notebooks: tuple[str, ...]) -> None:
    expected = {"porto": 110, "agueda": 176}[city]
    base_output = ROOT / "outputs" / city
    folders = {
        "01": base_output / "01_pre_chunking",
        "03": base_output / "03_chunksAllText",
        "02": base_output / "02_test_512",
    }
    for key_name, folder in folders.items():
        excel = folder / f"results_smart_cities_{city}.xlsx"
        manifest_doc = json.loads((folder / "run_manifest.json").read_text(encoding="utf-8"))
        assert manifest_doc["excel_sha256"] == sha256(excel), f"Excel file changed: {folder}"
        for name_, recorded_hash in manifest_doc["inputs_sha256"].items():
            assert recorded_hash == sha256(ROOT / "data" / name_), f"Input changed: {name_}"
        notebook_name = notebooks[{"01": 0, "02": 1, "03": 2}[key_name]]
        assert manifest_doc["notebook_sources_sha256"] == hash_notebook_sources(
            ROOT / "notebooks" / notebook_name
        ), f"Notebook changed after the run: {notebook_name}"
        assert manifest_doc["helper_sha256"] == sha256(ROOT / "scripts" / "reproducibility.py"), (
            f"Helper changed after the run: {folder}"
        )
        print(f"{key_name}: Excel and manifest OK")

    base = folders["01"] / f"results_smart_cities_{city}.xlsx"
    official = folders["03"] / f"results_smart_cities_{city}.xlsx"
    test_name = folders["02"] / f"results_smart_cities_{city}.xlsx"
    validate_comparison(base, official, "128_direct_historical", "128_segmented_main")
    validate_comparison(official, test_name, "128_segmented_main", "512_segmented_exploratory")

    for key_name in ("03", "02"):
        folder = folders[key_name]
        qa = pd.read_excel(folder / "checks" / f"QA_embeddings_{city}.xlsx", sheet_name="Texts")
        limit = 512 if key_name == "02" else 128
        n_datasets = len(pd.read_excel(official, sheet_name="Post-argmax_original"))
        assert n_datasets == expected and len(qa) == expected + 24 and qa["coverage_ok"].all()
        assert (qa["max_chunk_tokens"] <= limit).all()
        assert (qa["embedding_norm"].sub(1).abs() < 1e-5).all()
        print(f"{city} {key_name}: {len(qa)} texts, full coverage, {int(qa['was_split'].sum())} segmented")

    for folder, file_name in (
        (folders["03"], f"truncation_correction_impact_{city}.xlsx"),
        (folders["03"], f"variation_128_vs_512_{city}.xlsx"),
    ):
        file_path = folder / "checks" / file_name
        comparison = pd.read_excel(file_path, sheet_name="Classification")
        assert (comparison["tfidf_same_%"] == 100).all(), f"Different TF-IDF: {file_path}"
        print(f"{file_name}: comparison and TF-IDF OK")

    for name_ in notebooks:
        n = nbformat.read(ROOT / "notebooks" / name_, as_version=4)
        codes = [c for c in n.cells if c.cell_type == "code"]
        assert [c.execution_count for c in codes] == list(range(1, len(codes) + 1)), name_
        assert not any(o.output_type == "error" for c in codes for o in c.outputs), name_
        print(f"{name_}: clean execution, {len(codes)} cells")

    from build_multidimensionality_summary import prepare_tables

    summary = folders["03"] / "checks" / f"multidimensionality_summary_{city}.xlsx"
    tables = prepare_tables(city)
    for sheet in ("States", "Global review", "MET-001"):
        pd.testing.assert_frame_equal(pd.read_excel(summary, sheet_name=sheet), tables[sheet])
    assert (folders["03"] / "checks" / f"multidimensionality_summary_{city}.md").is_file()
    print("Multidimensional summary: tables consistent with the main Excel file")


def main() -> None:
    check_city("porto", NOTEBOOKS)
    check_city("agueda", AGUEDA_NOTEBOOKS)


if __name__ == "__main__":
    main()
