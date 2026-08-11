    # Findings: HCP Decile Targeting & Field Force Allocation

## Executive Summary
Analysis of 500 real Medicare Part D prescribers (CMS public data) across
Oncology, Cardiology, and Neurology reveals significant specialty and
regional imbalance in prescribing volume, with direct implications for
field force resource allocation.

## Key Findings

**1. Cardiology dominates prescribing volume**
Cardiology represents 224 of 500 HCPs (45%) but 726,907 of 1,081,519
total TRx (67%) — average 3,245 TRx/HCP vs. Oncology's 920. 120 of 167
Tier 1 HCPs (72%) are Cardiologists.
Recommendation: tier within specialty rather than globally, to avoid
cardiology monopolizing high-priority targeting.

**2. South region is under-resourced relative to demand**
South requires an estimated 11.9 reps vs. ~5.2 for North/West despite
similar HCP counts — driven by a higher concentration of high-volume
prescribers.
Recommendation: prioritize South for headcount reallocation.

**3. Total estimated field force need: ~29 reps for 500 HCPs**
Based on a flat 40-visits/rep/month capacity assumption — a first-pass
planning estimate, not a final resourcing number.

## Methodology
- Source: CMS Medicare Part D Prescribers by Provider (public dataset)
- Segmentation: SQL window functions (NTILE, RANK) + Pandas qcut
- Visit targets: Tier 1 = 4/month, Tier 2 = 2/month, Tier 3 = 1/month
- Dashboards: Excel (PivotTables) and Power BI

## Limitations
- NRx/TRx ratio is an approximation (30-day fill proxy), not true
  new-vs-refill claims data
- Medicare Part D only reflects patients 65+/Medicare-enrolled,
  not total commercial prescribing volume
- Rep capacity (40 visits/month) is a simplifying assumption