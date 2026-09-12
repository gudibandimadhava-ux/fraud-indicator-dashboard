"""
Fraud Indicator Dashboard (Option C)
-------------------------------------
This is a Streamlit app. Streamlit turns a plain Python script into a
web dashboard -- every time a filter changes, Streamlit just re-runs
this file top to bottom with the new filter values.

Run it locally with:   streamlit run app.py
"""

import pandas as pd
import plotly.express as px
import streamlit as st

# =========================================================
# PAGE CONFIG -- must be the first Streamlit command
# =========================================================
st.set_page_config(
    page_title="Fraud Indicator Dashboard",
    page_icon="🔍",
    layout="wide",
)

# =========================================================
# LOAD DATA
# (these files were produced by data_prep.py -- run that first)
# =========================================================
@st.cache_data  # caches the data so it doesn't reload on every click
def load_data():
    claims = pd.read_csv("claims_clean.csv")
    indicators = pd.read_csv("indicators_clean.csv")
    return claims, indicators

claims, indicators = load_data()

st.title("🔍 Fraud Indicator Dashboard")
st.caption(
    "Business question: What fraud is happening, why, and what should the "
    "claims/fraud team do about it? | Data: synthetic course dataset"
)

# =========================================================
# SIDEBAR FILTERS (interactive, cross-filter everything below)
# =========================================================
st.sidebar.header("Filters")

claim_types = sorted(indicators["claim_type"].dropna().unique())
selected_types = st.sidebar.multiselect(
    "Claim type", claim_types, default=claim_types
)

channels = sorted(indicators["channel"].dropna().unique())
selected_channels = st.sidebar.multiselect(
    "Channel", channels, default=channels
)

review_statuses = sorted(indicators["review_status"].dropna().unique())
selected_statuses = st.sidebar.multiselect(
    "Review status", review_statuses, default=review_statuses
)

months = sorted(indicators["claim_month"].dropna().unique())
selected_months = st.sidebar.select_slider(
    "Claim month range",
    options=months,
    value=(months[0], months[-1]),
)

# Apply filters to the indicators table
mask = (
    indicators["claim_type"].isin(selected_types)
    & indicators["channel"].isin(selected_channels)
    & indicators["review_status"].isin(selected_statuses)
    & (indicators["claim_month"] >= selected_months[0])
    & (indicators["claim_month"] <= selected_months[1])
)
f_indicators = indicators[mask]

# Filter claims to the same claim_type/channel/month window for KPI consistency
claims_mask = (
    claims["claim_type"].isin(selected_types)
    & claims["channel"].isin(selected_channels)
    & (claims["claim_month"] >= selected_months[0])
    & (claims["claim_month"] <= selected_months[1])
)
f_claims = claims[claims_mask]

# =========================================================
# KPI CALCULATIONS
# =========================================================
total_claims = len(f_claims)
flagged_claims = (f_claims["fraud_flag"] == 1).sum()
fraud_flag_rate = (flagged_claims / total_claims * 100) if total_claims else 0

total_indicators = len(f_indicators)
avg_score = f_indicators["score"].mean() if total_indicators else 0

resolved = f_indicators[f_indicators["review_status"].isin(["Confirmed", "Cleared"])]
confirmed_rate = (
    (f_indicators["review_status"] == "Confirmed").sum() / len(resolved) * 100
    if len(resolved) > 0 else 0
)

exposure = f_claims.loc[f_claims["fraud_flag"] == 1, "claim_amount"].sum()

# =========================================================
# KPI CARDS
# =========================================================
st.subheader("What is happening?")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Claims (filtered)", f"{total_claims:,}")
k2.metric("Fraud Flag Rate", f"{fraud_flag_rate:.1f}%",
          help="Fraud-flagged claims ÷ total claims. Derived metric.")
k3.metric("Fraud Indicators Raised", f"{total_indicators:,}")
k4.metric("Avg. Fraud Score", f"{avg_score:.1f}",
          help="Average risk score (0-100) across raised indicators.")
k5.metric("Confirmed Rate", f"{confirmed_rate:.1f}%",
          help="Of indicators resolved (Confirmed or Cleared), % that were Confirmed fraud. Derived metric.")

st.metric("Claim Amount at Risk (fraud-flagged claims)", f"₹{exposure:,.0f}")

st.divider()

# =========================================================
# VISUAL 1 -- Trend: fraud indicators raised per month
# =========================================================
st.subheader("Why is it happening? — Trends & drivers")

col1, col2 = st.columns(2)

with col1:
    trend = f_indicators.groupby("claim_month").size().reset_index(name="indicator_count")
    fig1 = px.line(
        trend, x="claim_month", y="indicator_count", markers=True,
        title="Fraud Indicators Raised Over Time",
        labels={"claim_month": "Month", "indicator_count": "Indicators Raised"},
    )
    st.plotly_chart(fig1, use_container_width=True)
    st.caption("Takeaway: shows whether fraud activity is rising, falling, or seasonal.")

# =========================================================
# VISUAL 2 -- Bar: fraud rate by claim type
# =========================================================
with col2:
    by_type = (
        f_claims.groupby("claim_type")
        .agg(total=("claim_id", "count"), flagged=("fraud_flag", "sum"))
        .reset_index()
    )
    by_type["fraud_rate_pct"] = (by_type["flagged"] / by_type["total"] * 100).round(2)
    fig2 = px.bar(
        by_type.sort_values("fraud_rate_pct", ascending=False),
        x="claim_type", y="fraud_rate_pct",
        title="Fraud Flag Rate by Claim Type",
        labels={"claim_type": "Claim Type", "fraud_rate_pct": "Fraud Rate (%)"},
        text="fraud_rate_pct",
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Takeaway: identifies which claim types carry the highest fraud risk.")

col3, col4 = st.columns(2)

# =========================================================
# VISUAL 3 -- Bar: indicator type volume & average score
# =========================================================
with col3:
    by_indicator = (
        f_indicators.groupby("indicator_type")
        .agg(count=("indicator_id", "count"), avg_score=("score", "mean"))
        .reset_index()
        .sort_values("count", ascending=False)
    )
    fig3 = px.bar(
        by_indicator, x="indicator_type", y="count",
        color="avg_score", color_continuous_scale="Reds",
        title="Indicator Volume & Avg. Risk Score by Type",
        labels={"indicator_type": "Indicator Type", "count": "Number Raised",
                "avg_score": "Avg Score"},
    )
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("Takeaway: shows which fraud signal fires most, and how severe it tends to be.")

# =========================================================
# VISUAL 4 -- Funnel: review pipeline status
# =========================================================
with col4:
    status_order = ["Flagged", "Under Review", "Confirmed", "Cleared"]
    status_counts = (
        f_indicators["review_status"].value_counts()
        .reindex(status_order).fillna(0).reset_index()
    )
    status_counts.columns = ["review_status", "count"]
    fig4 = px.funnel(
        status_counts, x="count", y="review_status",
        title="Fraud Review Pipeline",
        labels={"count": "Number of Indicators", "review_status": "Stage"},
    )
    st.plotly_chart(fig4, use_container_width=True)
    st.caption("Takeaway: shows where cases are piling up in the review process.")

# =========================================================
# VISUAL 5 -- Bar: fraud rate by channel
# =========================================================
by_channel = (
    f_claims.groupby("channel")
    .agg(total=("claim_id", "count"), flagged=("fraud_flag", "sum"))
    .reset_index()
)
by_channel["fraud_rate_pct"] = (by_channel["flagged"] / by_channel["total"] * 100).round(2)
fig5 = px.bar(
    by_channel.sort_values("fraud_rate_pct", ascending=False),
    x="channel", y="fraud_rate_pct",
    title="Fraud Flag Rate by Sales Channel",
    labels={"channel": "Channel", "fraud_rate_pct": "Fraud Rate (%)"},
    text="fraud_rate_pct",
)
st.plotly_chart(fig5, use_container_width=True)
st.caption("Takeaway: shows whether certain acquisition channels bring in riskier business.")

st.divider()

# =========================================================
# DRILL-DOWN -- pick a claim type to see underlying records
# =========================================================
st.subheader("Drill-down: underlying records")
drill_type = st.selectbox("Choose a claim type to inspect", claim_types)
drill_df = f_indicators[f_indicators["claim_type"] == drill_type][
    ["claim_id", "indicator_type", "score", "review_status",
     "claim_amount", "status", "channel", "claim_month"]
].sort_values("score", ascending=False)
st.dataframe(drill_df, use_container_width=True)
st.caption(
    f"Showing {len(drill_df)} fraud-indicator records for claim type "
    f"'{drill_type}', sorted by risk score (highest first)."
)
