# Summary for the final text — Águeda

Values generated from the main analysis, with 176 datasets. Each row of the states corresponds to one anchor version and one method; the counts sum to 176.

## Post-argmax states (n)

| version | method | n_single_label | n_multi_label_candidate | n_transversal_candidate | n_indeterminate |
| --- | --- | --- | --- | --- | --- |
| original | Embeddings | 109 | 19 | 38 | 10 |
| original | TF-IDF | 108 | 18 | 33 | 17 |
| 50_words | Embeddings | 104 | 24 | 38 | 10 |
| 50_words | TF-IDF | 84 | 28 | 38 | 26 |
| 100_words | Embeddings | 114 | 14 | 38 | 10 |
| 100_words | TF-IDF | 86 | 15 | 51 | 24 |
| 150_words | Embeddings | 110 | 17 | 39 | 10 |
| 150_words | TF-IDF | 100 | 18 | 35 | 23 |

## Global flagging (n and %)

| version | n_within_method_uncertainty | n_cross_method_disagreement | n_review_global | pct_review_global |
| --- | --- | --- | --- | --- |
| original | 104 | 50 | 154 | 87.5 |
| 50_words | 125 | 33 | 158 | 89.8 |
| 100_words | 118 | 39 | 157 | 89.2 |
| 150_words | 109 | 34 | 143 | 81.2 |

`within_method_uncertainty` and `cross_method_disagreement` are disjoint in this rule; their sum is `review_global`. They are signals for possible future review, not errors or validated classes. A transversal state may result from a low range even with fewer than three dimensions within `delta_close`.

## Sensitivity of the global review, MET-001 (%)

| version | min_global_review_pct | max_global_review_pct |
| --- | --- | --- |
| original | 85.2 | 89.2 |
| 50_words | 89.2 | 90.9 |
| 100_words | 86.9 | 91.5 |
| 150_words | 79.5 | 84.7 |

The accompanying Excel file contains the six scores, states and candidate dimensions per dataset, version and method. The `Sources` sheet identifies the files used by SHA-256. The results are descriptions of alignment, not estimates of substantive validity.
