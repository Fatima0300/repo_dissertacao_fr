# Notebook environment

## Repository structure

```text
data/              immutable inputs of the analysis: snapshots and anchors (see data/README.md)
notebooks/         00_data_collection.ipynb; porto/ and agueda/ with three analysis notebooks each
scripts/           Python code: reproduction, checks and manifests;
                   data_collection/ (CKAN exports and generation of the anchors)
                   and api_keys.py (reading of API keys)
tests/             unit tests
outputs/           everything the code produces; created on the first run, can be regenerated
environment.yaml   conda environment (portable)
conda-win-64.lock  exact package versions of the reference run (Windows)
.env.example       template of the API keys; copy it to .env, which is never versioned
```

The rule is simple: the code reads `data/` and never writes in it; everything
it produces goes to `outputs/`.

## Installation and reproduction

`environment.yaml` installs the libraries used by the six notebooks with
`conda-forge` packages, including spaCy's Portuguese model `pt_core_news_sm`.
There is no need to install dependencies with `pip`.

In the **Miniforge Prompt** or in a PowerShell in which `conda` is available,
run the following from the root of this repository. To install on a system
supported by Miniforge, resolving the versions available on that platform:

```powershell
conda env create -f environment.yaml
conda activate dissertacao_fr
python scripts/reproduce.py
python scripts/check_results.py
```

On Windows `win-64`, to rebuild the **exact package versions** of the
reference run, use this command **instead of** `conda env create`
in an environment that has not yet been created:

```powershell
conda create -n dissertacao_fr --file conda-win-64.lock
conda activate dissertacao_fr
python scripts/reproduce.py
python scripts/check_results.py
python -m unittest discover -s tests -v
```

`environment.yaml` remains the portable option: dependency resolution may
choose different versions on other systems. The lockfile above is specific
to Windows; Linux and macOS will only have the same guarantee once they have
created and tested their own lockfiles.

If a previous attempt left the `dissertacao_fr` environment created, update
it instead of running `conda env create`:

```powershell
conda env update -n dissertacao_fr -f environment.yaml --prune
conda activate dissertacao_fr
```

Open the notebooks in `notebooks/porto/` or `notebooks/agueda/` and select the
Python kernel of the `dissertacao_fr` environment. Start Jupyter from the
**root of the repository**: the notebooks look for the input files relative to
the current working folder, in `data/`.

```powershell
jupyter lab
```

Run the notebooks in this order, always with **Kernel → Restart & Run All**:

1. `notebooks/porto/smart_cities_porto_01_pre_chunking.ipynb` — historical reference
   with truncation; produces `outputs/porto/01_pre_chunking/`.
2. `notebooks/porto/smart_cities_porto_02_test_512.ipynb` — exploratory analysis
   at 512 tokens; produces `outputs/porto/02_test_512/`.
3. `notebooks/porto/smart_cities_porto_03_chunksAllText.ipynb` — main analysis,
   with segmentation at 128 tokens; produces `outputs/porto/03_chunksAllText/` and compares it with the two
   previous configurations: with truncated encoding (Section 11.1) and with the
   512-token limit (Section 11.5).

For Águeda, run `notebooks/agueda/smart_cities_agueda_01_pre_chunking.ipynb`,
`smart_cities_agueda_02_test_512.ipynb` and `smart_cities_agueda_03_chunksAllText.ipynb`
in the same order. The corresponding results are saved in `outputs/agueda/01_pre_chunking/`,
`outputs/agueda/02_test_512/` and `outputs/agueda/03_chunksAllText/`.

The numbering of the files corresponds to the order of execution: notebooks 01 and 02
are independent of each other, and 03 needs the results of both for the
comparative tables.
`python scripts/reproduce.py` runs the six from clean kernels in that
order, first Porto and then Águeda. You can use `python scripts/reproduce.py agueda`
or `python scripts/reproduce.py porto` to reproduce only one municipality.
The comparisons fail when a previous result is missing or when the
manifests indicate different data, model or environment. Each outputs
folder contains `run_manifest.json` with hashes of the inputs and of the Excel file,
the model revision and the package versions.

The support code is gathered in `scripts/`: `reproduce.py` runs the
notebooks, `check_results.py` checks the artefacts and
`reproducibility.py` saves and validates the manifests. The results of the main
analysis for Porto are saved in `outputs/porto/03_chunksAllText/` and those for Águeda in
`outputs/agueda/03_chunksAllText/`; the historical and exploratory experiments are in the
subfolders indicated above.

The figures of Chapter 4 of the dissertation are produced by the `03` notebooks,
in the cells marked as **Figure 4.x (dissertation)**. Each one repeats the
design of the corresponding original chart (same data, colours and markers),
with the usable width of the dissertation's A4 page (15.5 cm) and a larger font, and is
exported at 300 dpi to `outputs/agueda/03_chunksAllText/dissertation_figures/` or
`outputs/porto/03_chunksAllText/dissertation_figures/` (ten figures per municipality; the file
name indicates the figure and the panel, for example `figure_4_6_b_margins_log.png`).
In this English version, numbers in the figures use a decimal point
(`DECIMAL_SEPARATOR = "."`). The other charts in the notebooks are only for
inspection and are not exported.

After the notebooks have run,
`scripts/build_multidimensionality_summary.py` produces, in
`outputs/porto/03_chunksAllText/checks/` and `outputs/agueda/03_chunksAllText/checks/`, an Excel file with states,
profiles and candidates by dataset and a Markdown file with compact tables for each
municipality. `scripts/reproduce.py` calls this
generator automatically at the end; it can also be run on its own.

The notebooks require these files in `data/`:

- `porto_tabela_mae_datasets.csv`
- `agueda_tabela_mae_datasets.csv`
- `texto_base.csv`
- `ancoras_v1_50_palavras.csv`
- `ancoras_v2_100_palavras.csv`
- `ancoras_v3_150_palavras.csv`

The six files are now in `data/`. The Porto table contains 110
records and indicates the Porto Open Data Portal as its source, with
`exported_at = 2026-06-12T15:34:32`. The file `texto_base.csv` is
encoded in Windows-1252; the notebooks' reader tries that encoding
before `latin-1`. The other required files are UTF-8.
Document in the dissertation the origin, the preparation and the reuse rights
of the anchor texts and of the metadata. The embedding model
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` is pinned to
revision `e8f8c211226b894fcb81acc59f3b34ba3efd5f42` and is downloaded on the
first run, so Internet access or a previously prepared local copy is
required. See `data/README.md` for the provenance and the
hashes of the snapshot.

The notebook `notebooks/00_data_collection.ipynb` documents how the two master
tables are exported from the CKAN APIs of the portals. It calls the modules in
`scripts/data_collection/` (`porto.py` and `agueda.py`) and writes to
`outputs/data_collection/`, never to `data/`. It is not needed to run the six
notebooks, which use the snapshots in `data/`: a new export produces a different
snapshot (different `exported_at` and possibly different records), and the
notebook compares it with the one used in the dissertation. Section 5 of the
same notebook documents the generation of the 50-, 100- and 150-word anchors
with the OpenAI API (`scripts/data_collection/anchors.py`, the code of the run
of 12-06-2026): it shows the prompt and checks the preserved anchors, and only
calls the API, which requires a key and has a cost, with `GENERATE_ANCHORS = True`.

The data files keep their original Portuguese names and content: the analysed
metadata and anchor texts are in Portuguese, and the notebooks process them in
that language (spaCy's Portuguese model, Portuguese stopword lists). Only the
code, the comments, the explanatory text and the output labels are in English.

The study measures coverage, agreement and sensitivity of automatic methods
applied to the **metadata** of the datasets. It does not estimate the substantive
accuracy of the assigned dimensions: human validation was reserved for future work.

## API keys

The CKAN APIs of Porto and Águeda are public. Only the optional regeneration of
the anchor texts (Section 5 of `notebooks/00_data_collection.ipynb`) needs a key,
`OPENAI_API_KEY`, which is read with `scripts.api_keys.get_api_key`, never from a
value written in the code. The function looks first for an environment variable of the operating
system and then for a `.env` file at the root of the repository:

```powershell
Copy-Item .env.example .env   # then fill in OPENAI_API_KEY=... in .env
# or, as a Windows user variable (takes effect in new terminals):
setx OPENAI_API_KEY "..."
```

`.env` is listed in `.gitignore` and must not be shared, committed or pasted
into a notebook. A key that has been exposed must be revoked in the provider's
dashboard and replaced.
