"""Runs the notebooks in the required order, from clean kernels.

Usage: conda activate dissertacao_fr; python scripts/reproduce.py [porto|agueda|both]
"""

import argparse
from pathlib import Path
import sys

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.build_multidimensionality_summary import main as build_summary


NOTEBOOKS = (
    "porto/smart_cities_porto_01_pre_chunking.ipynb",
    "porto/smart_cities_porto_02_test_512.ipynb",
    "porto/smart_cities_porto_03_chunksAllText.ipynb",
)
AGUEDA_NOTEBOOKS = (
    "agueda/smart_cities_agueda_01_pre_chunking.ipynb",
    "agueda/smart_cities_agueda_02_test_512.ipynb",
    "agueda/smart_cities_agueda_03_chunksAllText.ipynb",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("city", choices=("porto", "agueda", "both"), nargs="?", default="both")
    city = parser.parse_args().city
    names = (*NOTEBOOKS, *AGUEDA_NOTEBOOKS) if city == "both" else (
        NOTEBOOKS if city == "porto" else AGUEDA_NOTEBOOKS
    )
    for name in names:
        source = ROOT / "notebooks" / name
        print(f"Running {name}...", flush=True)
        notebook = nbformat.read(source, as_version=4)
        NotebookClient(
            notebook,
            timeout=1800,
            kernel_name="python3",
            allow_errors=False,
            resources={"metadata": {"path": str(ROOT)}},
        ).execute()
        nbformat.write(notebook, source)
        print(f"Completed: {name}", flush=True)
    if city in ("porto", "both"):
        build_summary("porto")
    if city in ("agueda", "both"):
        build_summary("agueda")


if __name__ == "__main__":
    main()
