"""
HCP Decile Targeting & Field Force Allocation Engine
File: python/hcp_segmentation.py

Loads hcp_prescriptions.csv, performs tier/decile segmentation,
aggregates sales potential by region/specialty, prints an executive
summary, and exports processed_hcp_targets.csv.

Run:
    python python/hcp_segmentation.py
"""

import os
import sys
import pandas as pd

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
INPUT_PATH = os.path.join("data", "hcp_prescriptions.csv")
OUTPUT_PATH = "processed_hcp_targets.csv"

TIER_LABELS = {
    1: "Tier 1 - High Priority",
    2: "Tier 2 - Medium Priority",
    3: "Tier 3 - Low Priority",
}

VISIT_TARGETS = {
    1: 4,  # Tier 1 -> 4 visits/month
    2: 2,  # Tier 2 -> 2 visits/month
    3: 1,  # Tier 3 -> 1 visit/month
}

REP_MONTHLY_CAPACITY = 40  # assumed max visits one rep can execute/month


def load_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        sys.exit(f"[ERROR] Input file not found: {path}")
    df = pd.read_csv(path)
    required_cols = {"hcp_id", "hcp_name", "region", "specialty", "trx_count", "nrx_count"}
    missing = required_cols - set(df.columns)
    if missing:
        sys.exit(f"[ERROR] Missing required columns: {missing}")
    return df


def segment_hcps(df: pd.DataFrame) -> pd.DataFrame:
    """Assign decile/tier rank based on trx_count using qcut (3 tiers = terciles)."""
    df = df.copy()

    # Rank 1 = highest TRx
    df["trx_rank"] = df["trx_count"].rank(method="min", ascending=False).astype(int)
    df["nrx_rank"] = df["nrx_count"].rank(method="min", ascending=False).astype(int)

    # Tier via pd.qcut on trx_count (descending order -> tier 1 = top third)
    # labels are applied to ascending bins, so we reverse labels to align
    # tier 1 with the highest-volume bucket.
    df["volume_tile"] = pd.qcut(
        df["trx_count"].rank(method="first"),  # rank(method='first') avoids duplicate-edge errors
        q=3,
        labels=[3, 2, 1],  # ascending trx -> tile 3,2,1 (low to high)
    ).astype(int)

    df["priority_tier"] = df["volume_tile"].map(TIER_LABELS)
    df["monthly_visit_target"] = df["volume_tile"].map(VISIT_TARGETS)
    df["nrx_to_trx_ratio"] = (df["nrx_count"] / df["trx_count"]).round(3)

    df = df.sort_values("trx_rank").reset_index(drop=True)
    return df


def regional_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("region")
        .agg(
            total_hcps=("hcp_id", "count"),
            total_trx_volume=("trx_count", "sum"),
            total_nrx_volume=("nrx_count", "sum"),
            total_monthly_visits_required=("monthly_visit_target", "sum"),
        )
        .reset_index()
    )
    summary["estimated_reps_needed"] = (
        summary["total_monthly_visits_required"] / REP_MONTHLY_CAPACITY
    ).round(2)
    return summary.sort_values("total_trx_volume", ascending=False)


def specialty_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby("specialty")
        .agg(
            hcp_count=("hcp_id", "count"),
            total_trx=("trx_count", "sum"),
            avg_trx_per_hcp=("trx_count", "mean"),
            tier1_count=("priority_tier", lambda s: (s == TIER_LABELS[1]).sum()),
        )
        .reset_index()
    )
    summary["avg_trx_per_hcp"] = summary["avg_trx_per_hcp"].round(1)
    return summary.sort_values("total_trx", ascending=False)


def print_executive_summary(df: pd.DataFrame, region_df: pd.DataFrame, specialty_df: pd.DataFrame):
    print("\n" + "=" * 70)
    print(" HCP DECILE TARGETING & FIELD FORCE ALLOCATION — EXECUTIVE SUMMARY")
    print("=" * 70)

    print(f"\nTotal HCPs analyzed: {len(df)}")
    print(f"Total TRx volume:    {df['trx_count'].sum():,}")
    print(f"Total NRx volume:    {df['nrx_count'].sum():,}")

    print("\n--- Tier Distribution ---")
    tier_counts = df["priority_tier"].value_counts().reindex(
        [TIER_LABELS[1], TIER_LABELS[2], TIER_LABELS[3]]
    )
    print(tier_counts.to_string())

    print("\n--- Top 5 Priority HCPs (Tier 1) ---")
    top5 = df[df["volume_tile"] == 1].head(5)[
        ["hcp_id", "hcp_name", "region", "specialty", "trx_count", "monthly_visit_target"]
    ]
    print(top5.to_string(index=False))

    print("\n--- Regional Workload Summary ---")
    print(region_df.to_string(index=False))

    print("\n--- Specialty Summary ---")
    print(specialty_df.to_string(index=False))

    total_visits = df["monthly_visit_target"].sum()
    total_reps = round(total_visits / REP_MONTHLY_CAPACITY, 2)
    print(f"\nTotal monthly visits required across all regions: {total_visits}")
    print(f"Estimated field reps needed (@ {REP_MONTHLY_CAPACITY} visits/rep/month): {total_reps}")
    print("=" * 70 + "\n")


def main():
    df = load_data(INPUT_PATH)
    segmented_df = segment_hcps(df)
    region_df = regional_summary(segmented_df)
    specialty_df = specialty_summary(segmented_df)

    print_executive_summary(segmented_df, region_df, specialty_df)

    segmented_df.to_csv(OUTPUT_PATH, index=False)
    print(f"[SUCCESS] Processed HCP targets exported to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()