# HCP Decile Targeting & Field Force Allocation Engine

Segments healthcare providers into priority tiers based on real prescription
volume, assigns sales rep visit targets, and calculates regional field force
workload.

## Data Source
Real data from CMS Medicare Part D Prescribers by Provider (public dataset):
https://data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers/medicare-part-d-prescribers-by-provider

Raw file is cleaned and reshaped via `python/clean_real_data.py` into
`data/hcp_prescriptions.csv`.

## Structure
- `raw/` — original CMS download (not tracked in Git — see .gitignore)
- `data/` — cleaned working dataset
- `sql/` — decile/tier segmentation SQL (NTILE, RANK window functions)
- `python/` — cleaning + segmentation scripts
- `excel/` — dashboard build guide

## Run
```bash
python python/clean_real_data.py
python python/hcp_segmentation.py
```