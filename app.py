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
import plotly.io as pio
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
# VISUAL THEME
# A small, deliberate palette for a risk/fraud console:
# navy = structure, amber = "pay attention", red = confirmed loss.
# =========================================================
NAVY = "#1B3A5C"
NAVY_DARK = "#122A45"
AMBER = "#C98A2C"
AMBER_LIGHT = "#E0AD5C"
RED = "#B23A48"
GREEN = "#3F7D6A"
SLATE = "#5B6472"
INK = "#232B38"
BG = "#F9FAFA"
CARD_BORDER = "#E4E7EC"

CHART_SEQUENCE = [NAVY, AMBER, RED, "#6E8CAE", "#8C6A3F"]
FUNNEL_COLORS = {
    "Flagged": AMBER,
    "Under Review": AMBER_LIGHT,
    "Confirmed": RED,
    "Cleared": GREEN,
}

pio.templates["fraud_theme"] = pio.templates["plotly_white"]
pio.templates["fraud_theme"].layout.update(
    font=dict(family="IBM Plex Sans, sans-serif", color=INK, size=13),
    title=dict(font=dict(family="IBM Plex Sans, sans-serif", size=16, color=INK)),
    colorway=CHART_SEQUENCE,
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    margin=dict(t=50, l=10, r=10, b=10),
)
pio.templates.default = "fraud_theme"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'IBM Plex Sans', sans-serif;
}}

.stApp {{
    background-color: {BG};
}}

/* Main title */
h1 {{
    color: {NAVY_DARK} !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px;
}}
h2, h3 {{
    color: {NAVY_DARK} !important;
    font-weight: 600 !important;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background-color: {NAVY_DARK};
}}
section[data-testid="stSidebar"] * {{
    color: #E8EDF3 !important;
}}
section[data-testid="stSidebar"] span[data-tag] {{
    background-color: {AMBER} !important;
    color: {INK} !important;
}}
section[data-testid="stSidebar"] span[data-tag] span {{
    color: {INK} !important;
}}
section[data-testid="stSidebar"] span[data-tag] button {{
    color: {INK} !important;
}}

/* KPI cards */
.kpi-card {{
    background-color: #FFFFFF;
    border: 1px solid {CARD_BORDER};
    border-left: 4px solid var(--accent, {NAVY});
    border-radius: 4px;
    padding: 14px 16px;
    height: 100%;
}}
.kpi-label {{
    font-size: 12.5px;
    color: {SLATE};
    font-weight: 500;
    margin-bottom: 4px;
}}
.kpi-value {{
    font-size: 26px;
    font-weight: 700;
    color: {INK};
    font-feature-settings: "tnum";
}}

/* Chart captions */
.chart-caption {{
    color: {SLATE};
    font-size: 13px;
    margin-top: -6px;
    margin-bottom: 18px;
}}

/* Section divider */
hr {{
    border-color: {CARD_BORDER} !important;
}}
</style>
""", unsafe_allow_html=True)


def kpi_card(label, value, accent=NAVY, help_text=None):
    """Render one KPI as a small flat card with a colored accent bar."""
    tooltip = f' title="{help_text}"' if help_text else ""
    st.markdown(
        f"""<div class="kpi-card" style="--accent:{accent}"{tooltip}>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
            </div>""",
        unsafe_allow_html=True,
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

st.title("Fraud Indicator Dashboard")
st.caption(
    "What fraud is happening, why, and what the claims/fraud team should do about it "
    "— synthetic course dataset"
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
with k1:
    kpi_card("Total Claims (filtered)", f"{total_claims:,}", accent=NAVY)
with k2:
    kpi_card("Fraud Flag Rate", f"{fraud_flag_rate:.1f}%", accent=AMBER,
              help_text="Fraud-flagged claims / total claims (derived)")
with k3:
    kpi_card("Fraud Indicators Raised", f"{total_indicators:,}", accent=NAVY)
with k4:
    kpi_card("Avg. Fraud Score", f"{avg_score:.1f}", accent=AMBER,
              help_text="Average risk score (0-100) across raised indicators")
with k5:
    kpi_card("Confirmed Rate", f"{confirmed_rate:.1f}%", accent=RED,
              help_text="Of resolved indicators, % that were Confirmed fraud (derived)")

st.write("")
kpi_card("Claim Amount at Risk (fraud-flagged claims)", f"₹{exposure:,.0f}", accent=RED)

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
        color_discrete_sequence=[NAVY],
    )
    fig1.update_traces(line_width=2.5, marker=dict(size=6, color=NAVY))
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
    by_type_sorted = by_type.sort_values("fraud_rate_pct", ascending=False)
    fig2 = px.bar(
        by_type_sorted,
        x="claim_type", y="fraud_rate_pct",
        title="Fraud Flag Rate by Claim Type",
        labels={"claim_type": "Claim Type", "fraud_rate_pct": "Fraud Rate (%)"},
        text="fraud_rate_pct",
    )
    fig2.update_traces(
        marker_color=CHART_SEQUENCE[: len(by_type_sorted)],
        marker_line_width=0, textposition="outside",
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
        color="avg_score", color_continuous_scale=[NAVY, AMBER, RED],
        title="Indicator Volume & Avg. Risk Score by Type",
        labels={"indicator_type": "Indicator Type", "count": "Number Raised",
                "avg_score": "Avg Score"},
    )
    fig3.update_traces(marker_line_width=0)
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
    fig4.update_traces(
        marker=dict(color=[FUNNEL_COLORS.get(s, NAVY) for s in status_counts["review_status"]])
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

by_channel_sorted = by_channel.sort_values("fraud_rate_pct", ascending=False)
fig5 = px.bar(
    by_channel_sorted,
    x="channel", y="fraud_rate_pct",
    title="Fraud Flag Rate by Sales Channel",
    labels={"channel": "Channel", "fraud_rate_pct": "Fraud Rate (%)"},
    text="fraud_rate_pct",
)
fig5.update_traces(
    marker_color=CHART_SEQUENCE[: len(by_channel_sorted)],
    marker_line_width=0, textposition="outside",
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
