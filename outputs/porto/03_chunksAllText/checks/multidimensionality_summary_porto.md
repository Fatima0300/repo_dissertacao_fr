# Summary for the final text — Porto

Values generated from the main analysis, with 110 datasets. Each row of the states corresponds to one anchor version and one method; the counts sum to 110.

## Post-argmax states (n)

| version | method | n_single_label | n_multi_label_candidate | n_transversal_candidate | n_indeterminate |
| --- | --- | --- | --- | --- | --- |
| original | Embeddings | 65 | 13 | 22 | 10 |
| original | TF-IDF | 64 | 9 | 23 | 14 |
| 50_words | Embeddings | 61 | 15 | 24 | 10 |
| 50_words | TF-IDF | 42 | 10 | 14 | 44 |
| 100_words | Embeddings | 63 | 13 | 24 | 10 |
| 100_words | TF-IDF | 43 | 13 | 13 | 41 |
| 150_words | Embeddings | 62 | 14 | 24 | 10 |
| 150_words | TF-IDF | 47 | 13 | 18 | 32 |

## Global flagging (n and %)

| version | n_within_method_uncertainty | n_cross_method_disagreement | n_review_global | pct_review_global |
| --- | --- | --- | --- | --- |
| original | 68 | 19 | 87 | 79.1 |
| 50_words | 84 | 11 | 95 | 86.4 |
| 100_words | 83 | 9 | 92 | 83.6 |
| 150_words | 82 | 6 | 88 | 80.0 |

`within_method_uncertainty` and `cross_method_disagreement` are disjoint in this rule; their sum is `review_global`. They are signals for possible future review, not errors or validated classes. A transversal state may result from a low range even with fewer than three dimensions within `delta_close`.

## Sensitivity of the global review, MET-001 (%)

| version | min_global_review_pct | max_global_review_pct |
| --- | --- | --- |
| original | 75.5 | 80.0 |
| 50_words | 85.5 | 86.4 |
| 100_words | 81.8 | 85.5 |
| 150_words | 78.2 | 80.9 |

The accompanying Excel file contains the six scores, states and candidate dimensions per dataset, version and method. The `Sources` sheet identifies the files used by SHA-256. The results are descriptions of alignment, not estimates of substantive validity.
