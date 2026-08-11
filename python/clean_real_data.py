"""
clean_real_data.py
Converts the raw CMS Medicare Part D Prescribers-by-Provider file
into the project's standard schema:
hcp_id, hcp_name, region, specialty, trx_count, nrx_count

Source: https://data.cms.gov/provider-summary-by-type-of-service/
        medicare-part-d-prescribers/medicare-part-d-prescribers-by-provider
"""

import pandas as pd
import numpy as np

RAW_PATH = "raw/cms_part_d_prescribers.csv"
OUTPUT_PATH = "data/hcp_prescriptions.csv"

# CMS state -> simplified US region mapping
REGION_MAP = {
    **dict.fromkeys(["NY","NJ","PA","CT","MA","RI","VT","NH","ME"], "East"),
    **dict.fromkeys(["CA","OR","WA","NV","AZ","UT","CO","ID","MT","WY"], "West"),
    **dict.fromkeys(["IL","OH","MI","WI","MN","IN","IA","MO","ND","SD","NE","KS"], "North"),
    **dict.fromkeys(["TX","FL","GA","NC","SC","VA","TN","AL","MS","LA","AR","OK","KY","WV"], "South"),
}

TARGET_SPECIALTIES = ["Hematology-Oncology", "Cardiology", "Neurology"]
SPECIALTY_CLEAN = {
    "Hematology-Oncology": "Oncology",
    "Cardiology": "Cardiology",
    "Neurology": "Neurology",
}

# CMS files are large — read only needed columns
usecols = [
    "Prscrbr_NPI", "Prscrbr_Last_Org_Name", "Prscrbr_First_Name",
    "Prscrbr_State_Abrvtn", "Prscrbr_Type",
    "Tot_Clms", "Tot_30day_Fills"
]

print("Reading raw CMS file (this may take a minute for large files)...")
df = pd.read_csv(RAW_PATH, usecols=usecols, low_memory=False)

# Filter to target specialties only
df = df[df["Prscrbr_Type"].isin(TARGET_SPECIALTIES)].copy()

# Drop rows with missing/suppressed claim counts
df = df.dropna(subset=["Tot_Clms"])
df["Tot_Clms"] = df["Tot_Clms"].astype(int)

# Map to project schema
df["hcp_id"] = "HCP" + df["Prscrbr_NPI"].astype(str)
df["hcp_name"] = "Dr. " + df["Prscrbr_First_Name"].fillna("") + " " + df["Prscrbr_Last_Org_Name"].fillna("")
df["region"] = df["Prscrbr_State_Abrvtn"].map(REGION_MAP).fillna("South")
df["specialty"] = df["Prscrbr_Type"].map(SPECIALTY_CLEAN)
df["trx_count"] = df["Tot_Clms"]

# NRx isn't published in this CMS file (privacy-suppressed at new/refill split),
# so approximate new-prescription share using 30-day fill ratio as a realistic proxy
df["nrx_count"] = (df["Tot_30day_Fills"].fillna(df["trx_count"] * 0.3) * 0.22).round().astype(int)
df["nrx_count"] = np.minimum(df["nrx_count"], df["trx_count"] - 1).clip(lower=1)

final_df = df[["hcp_id", "hcp_name", "region", "specialty", "trx_count", "nrx_count"]]

# Take a manageable, realistic sample (adjust n as needed)
final_df = final_df.sample(n=min(500, len(final_df)), random_state=42).reset_index(drop=True)

final_df.to_csv(OUTPUT_PATH, index=False)
print(f"Cleaned dataset saved to {OUTPUT_PATH} — {len(final_df)} real HCP records.")