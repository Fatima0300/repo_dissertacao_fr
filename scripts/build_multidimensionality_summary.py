"""Prepares compact tables per municipality from the exported results."""

from __future__ import annotations

import ast
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.reproducibility import hash_notebook_sources, sha256

VERSIONS = ("original", "50_words", "100_words", "150_words")
def file_paths(city: str) -> tuple[Path, Path, Path, Path]:
    if city not in ("porto", "agueda"):
        raise ValueError(city)
    base = ROOT / "outputs" / city / "03_chunksAllText"
    excel = base / f"results_smart_cities_{city}.xlsx"
    destination = base / "checks"
    impact = destination / f"truncation_correction_impact_{city}.xlsx"
    notebook = ROOT / "notebooks" / ("agueda" if city == "agueda" else "porto") / f"smart_cities_{city}_03_chunksAllText.ipynb"
    return excel, impact, destination, notebook


def check_source(city: str = "porto") -> None:
    EXCEL, _, _, notebook = file_paths(city)
    manifest_doc = json.loads((EXCEL.parent / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest_doc["experiment"] == "128_segmented_main"
    assert manifest_doc["excel_sha256"] == sha256(EXCEL), "Main Excel file changed after the run"
    assert manifest_doc["notebook_sources_sha256"] == hash_notebook_sources(
        notebook
    ), "Main notebook changed after the run"
    assert manifest_doc["helper_sha256"] == sha256(ROOT / "scripts" / "reproducibility.py")


def prepare_tables(city: str = "porto") -> dict[str, pd.DataFrame]:
    EXCEL, IMPACT, _, _ = file_paths(city)
    check_source(city)
    states = pd.read_excel(EXCEL, sheet_name="Post-argmax summary")
    global_ = pd.read_excel(EXCEL, sheet_name="Post-argmax global review")
    sens = pd.read_excel(EXCEL, sheet_name="Post-argmax sensitivity")
    impact = pd.read_excel(IMPACT, sheet_name="Impact")
    clustering = pd.read_excel(IMPACT, sheet_name="Clustering")

    assert set(states["version"]) == set(global_["version"]) == set(VERSIONS)
    assert set(states["method"]) == {"Embeddings", "TF-IDF"}
    n_datasets = int(states["n_datasets"].iloc[0])
    assert (states["n_datasets"] == n_datasets).all() and (global_["n_datasets"] == n_datasets).all()
    assert (states[[f"n_{s}" for s in (
        "single_label", "multi_label_candidate", "transversal_candidate", "indeterminate"
    )]].sum(axis=1) == n_datasets).all()
    assert (global_["n_within_method_uncertainty"] + global_["n_cross_method_disagreement"]
            == global_["n_review_global"]).all()

    profiles = []
    for version in VERSIONS:
        tab = pd.read_excel(EXCEL, sheet_name=f"Post-argmax_{version}", dtype={"dataset_id": str})
        assert len(tab) == n_datasets and tab["dataset_id"].is_unique
        for suf, method in (("emb", "Embeddings"), ("tfidf", "TF-IDF")):
            score_cols = sorted(c for c in tab if c.startswith(f"score_{suf}_"))
            assert len(score_cols) == 6, (version, method, score_cols)
            labels_list = tab[f"candidate_labels_{suf}"].map(ast.literal_eval)
            assert labels_list.map(len).eq(tab[f"n_candidate_labels_{suf}"]).all()
            valid_mask = tab[f"status_{suf}"] != "indeterminate"
            assert tab.loc[valid_mask, f"n_candidate_labels_{suf}"].eq(
                tab.loc[valid_mask, f"n_close_{suf}"]
            ).all()
            assert labels_list[~valid_mask].map(len).eq(0).all()
            assert tab["review_global"].eq(
                tab["review_emb"] | tab["review_tfidf"] | tab["discordant_single"]
            ).all()
            cols = ["dataset_id", "dataset_title", f"top1_label_{suf}",
                    f"top1_score_{suf}", f"margin_12_{suf}", f"score_range_{suf}",
                    f"n_close_{suf}", f"status_{suf}", f"candidate_labels_{suf}",
                    "discordant_single", "review_global"] + score_cols
            p = tab[cols].copy()
            p.insert(2, "version", version)
            p.insert(3, "method", method)
            p.columns = [
                c.replace(f"score_{suf}_", "score_") if c.startswith(f"score_{suf}_")
                else c.removesuffix(f"_{suf}") for c in p.columns
            ]
            profiles.append(p)
    profiles_df = pd.concat(profiles, ignore_index=True)

    met001 = (sens.groupby("version", sort=False)["Global review (%)"]
              .agg(["min", "max"]).reset_index()
              .rename(columns={"min": "min_global_review_pct", "max": "max_global_review_pct"}))
    return {
        "States": states,
        "Global review": global_,
        "Profiles and candidates": profiles_df,
        "MET-001": met001,
        "Truncation impact": impact,
        "Clustering": clustering,
        "Sources": pd.DataFrame([
            {"file": str(EXCEL.relative_to(ROOT)), "sha256": sha256(EXCEL)},
            {"file": str(IMPACT.relative_to(ROOT)), "sha256": sha256(IMPACT)},
        ]),
    }


def md_table(df: pd.DataFrame) -> str:
    column_names = list(df.columns)
    rows_data = ["| " + " | ".join(column_names) + " |", "| " + " | ".join("---" for _ in column_names) + " |"]
    for values_ in df.itertuples(index=False, name=None):
        rows_data.append("| " + " | ".join(str(v).replace("|", "/") for v in values_) + " |")
    return "\n".join(rows_data)


def main(city: str = "porto") -> None:
    EXCEL, _, DESTINATION, _ = file_paths(city)
    tables = prepare_tables(city)
    DESTINATION.mkdir(parents=True, exist_ok=True)
    excel = DESTINATION / f"multidimensionality_summary_{city}.xlsx"
    with pd.ExcelWriter(excel) as writer:
        for name_, df in tables.items():
            df.to_excel(writer, sheet_name=name_, index=False)

    e = tables["States"]
    g = tables["Global review"]
    rows_state = e[["version", "method", "n_single_label", "n_multi_label_candidate",
                       "n_transversal_candidate", "n_indeterminate"]].copy()
    rows_global = g[["version", "n_within_method_uncertainty",
                       "n_cross_method_disagreement", "n_review_global",
                       "pct_review_global"]].copy()
    text_value = (
        f"# Summary for the final text — {'Águeda' if city == 'agueda' else 'Porto'}\n\n"
        f"Values generated from the main analysis, with {int(e['n_datasets'].iloc[0])} datasets. Each row of the states "
        f"corresponds to one anchor version and one method; the counts sum to {int(e['n_datasets'].iloc[0])}.\n\n"
        "## Post-argmax states (n)\n\n" + md_table(rows_state) + "\n\n"
        "## Global flagging (n and %)\n\n" + md_table(rows_global) + "\n\n"
        "`within_method_uncertainty` and `cross_method_disagreement` are disjoint in this rule; "
        "their sum is `review_global`. They are signals for possible future review, not errors "
        "or validated classes. A transversal state may result from a low range "
        "even with fewer than three dimensions within `delta_close`.\n\n"
        "## Sensitivity of the global review, MET-001 (%)\n\n"
        + md_table(tables["MET-001"]) + "\n\n"
        "The accompanying Excel file contains the six scores, states and candidate dimensions per dataset, "
        "version and method. The `Sources` sheet identifies the files used by SHA-256. "
        "The results are descriptions of alignment, not estimates of substantive validity.\n"
    )
    markdown = DESTINATION / f"multidimensionality_summary_{city}.md"
    markdown.write_text(text_value, encoding="utf-8")
    print(f"Summary created: {excel} and {markdown}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("city", choices=("porto", "agueda", "both"), nargs="?", default="both")
    choice = parser.parse_args().city
    for city in (("porto", "agueda") if choice == "both" else (choice,)):
        main(city)
