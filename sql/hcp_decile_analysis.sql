/* ============================================================
   HCP DECILE TARGETING & FIELD FORCE ALLOCATION ENGINE
   File: sql/hcp_decile_analysis.sql
   Purpose: Segment HCPs into priority tiers using window functions,
            assign visit targets, and roll up workload by region.
   Compatible with: PostgreSQL / Snowflake / SQL Server (minor tweaks
   noted for NTILE/RANK dialects where relevant)
   ============================================================ */

-- ------------------------------------------------------------
-- 0. SOURCE TABLE (assumes hcp_prescriptions.csv loaded as-is)
-- ------------------------------------------------------------
-- CREATE TABLE hcp_prescriptions (
--     hcp_id      VARCHAR(10),
--     hcp_name    VARCHAR(100),
--     region      VARCHAR(20),
--     specialty   VARCHAR(30),
--     trx_count   INT,
--     nrx_count   INT
-- );

-- ------------------------------------------------------------
-- 1. TIER SEGMENTATION (NTILE + RANK)
-- ------------------------------------------------------------
WITH ranked_hcps AS (
    SELECT
        hcp_id,
        hcp_name,
        region,
        specialty,
        trx_count,
        nrx_count,
        -- NTILE(3) splits doctors into 3 equal-sized buckets by TRx volume
        NTILE(3) OVER (ORDER BY trx_count DESC) AS volume_tile,
        -- RANK() preserves ties and gives a global priority rank
        RANK() OVER (ORDER BY trx_count DESC) AS trx_rank,
        RANK() OVER (ORDER BY nrx_count DESC) AS nrx_rank
    FROM hcp_prescriptions
),

tiered_hcps AS (
    SELECT
        *,
        CASE
            WHEN volume_tile = 1 THEN 'Tier 1 - High Priority'
            WHEN volume_tile = 2 THEN 'Tier 2 - Medium Priority'
            ELSE 'Tier 3 - Low Priority'
        END AS priority_tier,
        CASE
            WHEN volume_tile = 1 THEN 4
            WHEN volume_tile = 2 THEN 2
            ELSE 1
        END AS monthly_visit_target
    FROM ranked_hcps
)

SELECT
    hcp_id,
    hcp_name,
    region,
    specialty,
    trx_count,
    nrx_count,
    ROUND(nrx_count * 1.0 / NULLIF(trx_count, 0), 3) AS nrx_to_trx_ratio,
    volume_tile,
    priority_tier,
    monthly_visit_target,
    trx_rank,
    nrx_rank
FROM tiered_hcps
ORDER BY trx_rank;


-- ------------------------------------------------------------
-- 2. REGIONAL ROLL-UP: PROJECTED VOLUME & REP WORKLOAD
-- ------------------------------------------------------------
WITH ranked_hcps AS (
    SELECT
        hcp_id, region, specialty, trx_count, nrx_count,
        NTILE(3) OVER (ORDER BY trx_count DESC) AS volume_tile
    FROM hcp_prescriptions
),

tiered_hcps AS (
    SELECT
        *,
        CASE
            WHEN volume_tile = 1 THEN 'Tier 1 - High Priority'
            WHEN volume_tile = 2 THEN 'Tier 2 - Medium Priority'
            ELSE 'Tier 3 - Low Priority'
        END AS priority_tier,
        CASE
            WHEN volume_tile = 1 THEN 4
            WHEN volume_tile = 2 THEN 2
            ELSE 1
        END AS monthly_visit_target
    FROM ranked_hcps
)

SELECT
    region,
    COUNT(*)                                   AS total_hcps,
    SUM(trx_count)                              AS total_trx_volume,
    SUM(nrx_count)                              AS total_nrx_volume,
    SUM(CASE WHEN priority_tier = 'Tier 1 - High Priority' THEN 1 ELSE 0 END)   AS tier1_hcp_count,
    SUM(CASE WHEN priority_tier = 'Tier 2 - Medium Priority' THEN 1 ELSE 0 END) AS tier2_hcp_count,
    SUM(CASE WHEN priority_tier = 'Tier 3 - Low Priority' THEN 1 ELSE 0 END)    AS tier3_hcp_count,
    SUM(monthly_visit_target)                   AS total_monthly_visits_required,
    -- Assuming a rep can realistically execute ~40 visits/month
    ROUND(SUM(monthly_visit_target) * 1.0 / 40, 2) AS estimated_reps_needed
FROM tiered_hcps
GROUP BY region
ORDER BY total_trx_volume DESC;


-- ------------------------------------------------------------
-- 3. SPECIALTY-LEVEL SUMMARY (supporting view for Excel/BI tools)
-- ------------------------------------------------------------
WITH ranked_hcps AS (
    SELECT
        specialty, trx_count, nrx_count,
        NTILE(3) OVER (ORDER BY trx_count DESC) AS volume_tile
    FROM hcp_prescriptions
)
SELECT
    specialty,
    COUNT(*)               AS hcp_count,
    SUM(trx_count)          AS total_trx,
    ROUND(AVG(trx_count),1) AS avg_trx_per_hcp,
    SUM(CASE WHEN volume_tile = 1 THEN 1 ELSE 0 END) AS tier1_count
FROM ranked_hcps
GROUP BY specialty
ORDER BY total_trx DESC;