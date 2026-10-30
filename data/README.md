# Data used in the Porto and Águeda notebooks

The notebooks analyse the **metadata** of the datasets, not the associated
resource files. The snapshot `porto_tabela_mae_datasets.csv` has 110
records with unique IDs; its columns indicate the Porto Open Data Portal as
the source and `exported_at = 2026-06-12T15:34:32`. The `license` column
contains 108 «Creative Commons CCZero» values and two «Open Data Commons Open
Database License (ODbL)» values. When redistributing the snapshot or derived
files, check and document the conditions applicable to each record.

`agueda_tabela_mae_datasets.csv` has 176 records and is read by the three
notebooks in `notebooks/agueda/`. Here too, metadata are analysed, with
the same four anchor versions. The origin and the reuse conditions of the
Águeda snapshot must be documented from its metadata and from the collection
source before external publication.

The four anchor versions have six dimensions each. `texto_base.csv` is
in Windows-1252, with the separator `;`, and is read with that encoding (cp1252),
so that the «€» and «‰» symbols of the original anchors are preserved; the other four CSV files used for Porto
are in UTF-8. According to information provided by the supervision, the base text
comes from the document of the [Estratégia Nacional de Territórios Inteligentes
(ENTI)](https://digital.gov.pt/documentos/estrategia-nacional-de-territorios-inteligentes)
(National Strategy for Smart Territories).
The 50-, 100- and 150-word versions were generated with the gpt-5.4-mini model,
through OpenAI's Responses API (18 calls: one per dimension and per
version, recorded on 12-06-2026). The full prompt is reproduced in
Appendix A of the dissertation, and the code of that run is in
`scripts/data_collection/anchors.py` and in Section 5 of
`notebooks/00_data_collection.ipynb`, which also compares the length of each
anchor with the interval requested in the prompt (16 of the 18 anchors are
within it; the two exceptions are in the 150-word version). The generation read
`texto_base.csv` in latin-1, so the «€» and «‰» of the base text reached the
model as control characters. `temperature`, `top_p` and the seed were not
fixed, so a new call may not reproduce the same texts: the
analysis is reproducible from the versions preserved in these CSV files, whose
hashes below pin the inputs used, but the generation step is not fully
reproducible. The identification of the specific edition of the ENTI document and of the
source passages remains to be confirmed.

The files keep their original Portuguese names and content (Portuguese metadata
and anchor texts); they were not translated.

## Immutable snapshot — SHA-256

| File | SHA-256 |
| --- | --- |
| `porto_tabela_mae_datasets.csv` | `4f0138ca2075e2c27d2e009b802b948a83c2decf4f71f2c57fa888f6e1d1cc60` |
| `agueda_tabela_mae_datasets.csv` | `025aef4bab24645d7150b3e65732ef21f0b6501e3dfd0f50c2d78ae75a7bb94b` |
| `texto_base.csv` | `ccd9b11e367b07c47212b64c5bc04cd6dca9df3c6da35bc4b6d8290a7ad4b29b` |
| `ancoras_v1_50_palavras.csv` | `66658f4530b50811928f118d76a919c1e81e1204acb7a6fa7459f0f77b29796d` |
| `ancoras_v2_100_palavras.csv` | `3a8b1fae634e98577b8b65845adecfd8517d9a81b21cdc38009d7b0b3e864048` |
| `ancoras_v3_150_palavras.csv` | `8f2c8c3127e4f34183af5526e7f085ad7a1854fb0897736d26a301a1435066b0` |

`ancoras_llm_3_versoes.csv` is the direct output of the 18 calls and is not read
by the six notebooks; the three `ancoras_v*_palavras.csv` files are its subsets,
one per version. The Porto and Águeda results are produced by separate workflows
with the same anchors; comparisons between municipalities must take into account the
different composition and size of the two catalogues.
