"""
Data preparation for the Fraud Indicator Dashboard (Option C).

What this script does, in plain terms:
1. Loads claims.csv, fraud_indicators.csv, policies.csv
2. Joins them together so every fraud indicator record also has
   claim details (amount, type, status) and policy details (channel)
3. Cleans a few known issues (see comments below)
4. Calculates the KPIs we'll show on the dashboard
5. Saves two clean files that app.py will read:
   - claims_clean.csv   (one row per claim, with fraud_flag)
   - indicators_clean.csv (one row per fraud indicator, joined to claim+policy info)
"""

import pandas as pd

# ---------- 1. Load raw data ----------
claims = pd.read_csv("data/claims.csv")
fraud = pd.read_csv("data/fraud_indicators.csv")
policies = pd.read_csv("data/policies.csv")

# ---------- 2. Clean claims ----------
# claim_date comes in as text -> convert to a real date so we can do trends
claims["claim_date"] = pd.to_datetime(claims["claim_date"])
claims["claim_month"] = claims["claim_date"].dt.to_period("M").astype(str)

# days_to_settle is only filled in for Settled claims (null for Pending/Rejected)
# -- this is expected, NOT a data error, so we just leave the nulls as-is
# and remember to filter to status == 'Settled' whenever we average this column.

# ---------- 3. Join claims -> policies to bring in "channel" ----------
# premium/channel live at policy level, so we merge on policy_id
claims_with_channel = claims.merge(
    policies[["policy_id", "channel", "product_name"]],
    on="policy_id",
    how="left",
)

# ---------- 4. Join fraud indicators -> claims (+channel) ----------
# Not every claim has an indicator row (indicators only exist for claims that
# triggered a rule) -- so we use a LEFT join from indicators to claims,
# keeping every indicator record and attaching its claim's details.
indicators_full = fraud.merge(
    claims_with_channel[
        ["claim_id", "claim_type", "claim_amount", "status",
         "fraud_flag", "claim_month", "channel"]
    ],
    on="claim_id",
    how="left",
)

# ---------- 5. Save clean files for the dashboard ----------
claims_with_channel.to_csv("data/claims_clean.csv", index=False)
indicators_full.to_csv("data/indicators_clean.csv", index=False)

# ---------- 6. Quick KPI printout (sanity check) ----------
total_claims = len(claims_with_channel)
flagged_claims = (claims_with_channel["fraud_flag"] == 1).sum()
fraud_flag_rate = flagged_claims / total_claims * 100

total_indicators = len(indicators_full)
avg_score = indicators_full["score"].mean()

resolved = indicators_full[indicators_full["review_status"].isin(["Confirmed", "Cleared"])]
confirmed_rate = (
    (indicators_full["review_status"] == "Confirmed").sum() / len(resolved) * 100
    if len(resolved) > 0 else 0
)

flagged_exposure = claims_with_channel.loc[
    claims_with_channel["fraud_flag"] == 1, "claim_amount"
].sum()

print("=== KPI sanity check ===")
print(f"Total claims:              {total_claims:,}")
print(f"Fraud-flagged claims:      {flagged_claims:,}")
print(f"Fraud flag rate:           {fraud_flag_rate:.2f}%")
print(f"Total fraud indicators:    {total_indicators:,}")
print(f"Average fraud score:       {avg_score:.1f}")
print(f"Confirmed rate (resolved): {confirmed_rate:.1f}%")
print(f"Claim amount at risk:      Rs {flagged_exposure:,.0f}")
print()
print("Saved: data/claims_clean.csv, data/indicators_clean.csv")
