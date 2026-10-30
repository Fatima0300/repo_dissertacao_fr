"""Collection of the inputs of the analysis through APIs.

`porto` and `agueda` export the master tables of the open data portals (CKAN
APIs), each with `export_master_table(output_file)`. `anchors` holds the
generation of the anchor texts with the OpenAI API (run of 12-06-2026).
`snapshot` protects the immutable inputs in data/ and compares a new export
with them. Everything is called by notebooks/00_data_collection.ipynb; the
analysis notebooks do not use this package.
"""
