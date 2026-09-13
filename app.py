"""
Fraud Indicator Dashboard (Option C)
-------------------------------------
This is a Streamlit app. Streamlit turns a plain Python script into a
web dashboard -- every time a filter changes, Streamlit just re-runs
this file top to bottom with the new filter values.

Run it locally with:   streamlit run app.py
"""

import base64
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
    initial_sidebar_state="collapsed",
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
    transition=dict(duration=400, easing="cubic-in-out"),
    hoverlabel=dict(font_family="IBM Plex Sans, sans-serif", font_size=13),
)
pio.templates.default = "fraud_theme"

def add_depth(fig):
    """Give bar/funnel traces a subtle beveled edge so they read with a little more depth."""
    fig.update_traces(
        selector=dict(type="bar"),
        marker_line_width=1, marker_line_color="rgba(255,255,255,0.55)",
    )
    fig.update_traces(
        selector=dict(type="funnel"),
        marker_line_width=1, marker_line_color="rgba(255,255,255,0.55)",
        connector=dict(line=dict(width=0)),
    )
    fig.update_layout(transition=dict(duration=400, easing="cubic-in-out"))
    return fig

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'IBM Plex Sans', sans-serif;
}}

.stApp {{
    background-color: {BG};
}}

/* Gentle one-time entrance -- content eases up into place on load */
@keyframes riseIn {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
.main .block-container > div {{
    animation: riseIn 0.5s ease-out both;
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

/* Sidebar (still used by Streamlit for the collapse arrow / mobile nav) */
section[data-testid="stSidebar"] {{
    background-color: {NAVY_DARK};
}}

/* Filter bar label sits above Streamlit's native bordered container */
.filter-bar-label {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.6px;
    color: {SLATE};
    margin-bottom: 6px;
}}
div[data-testid="stMultiSelect"] span[data-tag] {{
    background-color: {AMBER} !important;
    color: {INK} !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}}
div[data-testid="stMultiSelect"] span[data-tag]:hover {{
    transform: translateY(-1px);
    box-shadow: 0 3px 8px rgba(0,0,0,0.18);
}}
div[data-testid="stMultiSelect"] span[data-tag] span,
div[data-testid="stMultiSelect"] span[data-tag] button {{
    color: {INK} !important;
}}

/* KPI cards -- layered shadow gives real lift, not a flat drop-shadow */
.kpi-card {{
    background-color: #FFFFFF;
    border: 1px solid {CARD_BORDER};
    border-left: 4px solid var(--accent, {NAVY});
    border-radius: 6px;
    padding: 14px 16px;
    height: 100%;
    box-shadow: 0 1px 2px rgba(16,24,40,0.04), 0 1px 3px rgba(16,24,40,0.06);
    transition: transform 0.22s cubic-bezier(.2,.8,.2,1),
                box-shadow 0.22s cubic-bezier(.2,.8,.2,1);
    will-change: transform;
}}
.kpi-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 10px 20px rgba(16,24,40,0.10), 0 4px 8px rgba(16,24,40,0.08);
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
    transition: color 0.2s ease;
}}

/* Chart containers -- subtle lift + shadow on hover, same easing as KPI cards */
div[data-testid="stPlotlyChart"] {{
    border-radius: 6px;
    transition: box-shadow 0.25s cubic-bezier(.2,.8,.2,1),
                transform 0.25s cubic-bezier(.2,.8,.2,1);
}}
div[data-testid="stPlotlyChart"]:hover {{
    box-shadow: 0 12px 24px rgba(16,24,40,0.10);
    transform: translateY(-2px);
}}

/* Byline -- small author credit under the title */
.byline {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 14px 0 20px 0;
}}
.byline-photo {{
    width: 42px;
    height: 42px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid {CARD_BORDER};
}}
.byline-name {{
    font-size: 14px;
    font-weight: 600;
    color: {INK};
}}
.byline-meta {{
    font-size: 12.5px;
    color: {SLATE};
}}

/* Executive insight banner -- the headline finding, always visible up top */
.insight-banner {{
    background: linear-gradient(135deg, {NAVY} 0%, {NAVY_DARK} 100%);
    border-radius: 8px;
    padding: 18px 24px;
    margin: 4px 0 24px 0;
    display: flex;
    align-items: center;
    gap: 22px;
    box-shadow: 0 4px 14px rgba(18,42,69,0.20);
}}
.insight-number {{
    font-size: 40px;
    font-weight: 700;
    color: {AMBER_LIGHT};
    line-height: 1;
    white-space: nowrap;
}}
.insight-text {{
    color: #E8EDF3;
    font-size: 14.5px;
    line-height: 1.5;
}}
.insight-text b {{
    color: #FFFFFF;
}}

/* Benchmark reference line label */
.js-plotly-plot .annotation-text {{
    font-weight: 600 !important;
}}

/* Smooth scrolling for the anchor-link navigation */
html {{
    scroll-behavior: smooth;
}}

/* Quick nav -- jump links under the title */
.quick-nav {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin: 4px 0 22px 0;
}}
.quick-nav a {{
    text-decoration: none;
    background-color: #FFFFFF;
    border: 1px solid {CARD_BORDER};
    color: {NAVY_DARK};
    font-size: 13px;
    font-weight: 500;
    padding: 6px 14px;
    border-radius: 999px;
    transition: transform 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}}
.quick-nav a:hover {{
    background-color: {NAVY};
    color: #FFFFFF;
    transform: translateY(-2px);
    box-shadow: 0 6px 14px rgba(16,24,40,0.15);
}}

/* Scroll-margin so anchored sections don't hide under sticky chrome */
[id] {{
    scroll-margin-top: 20px;
}}

/* Floating back-to-top button */
.back-to-top {{
    position: fixed;
    bottom: 28px;
    right: 28px;
    background-color: {NAVY};
    color: #FFFFFF !important;
    width: 46px;
    height: 46px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    text-decoration: none;
    font-size: 20px;
    box-shadow: 0 4px 12px rgba(16,24,40,0.25);
    transition: transform 0.2s cubic-bezier(.2,.8,.2,1), box-shadow 0.2s ease, background-color 0.2s ease;
    z-index: 999;
}}
.back-to-top:hover {{
    transform: translateY(-4px);
    box-shadow: 0 10px 20px rgba(16,24,40,0.30);
    background-color: {NAVY_DARK};
}}

/* Section divider */
hr {{
    border-color: {CARD_BORDER} !important;
}}

/* Dataframe: smooth row highlight instead of a hard flat hover */
div[data-testid="stDataFrame"] * {{
    transition: background-color 0.12s ease;
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

st.markdown('<div id="top"></div>', unsafe_allow_html=True)
st.title("Fraud Indicator Dashboard")
st.caption(
    "What fraud is happening, why, and what the claims/fraud team should do about it "
    "- synthetic course dataset"
)

# ---------------------------------------------------------
# Byline -- identifies who this submission belongs to.
# Falls back to plain text if profile.jpg isn't found, so a
# missing photo never breaks the whole dashboard.
# ---------------------------------------------------------
try:
    with open("profile.jpg", "rb") as f:
        profile_b64 = base64.b64encode(f.read()).decode()
    st.markdown(f"""
    <div class="byline">
        <img src="data:image/jpeg;base64,{profile_b64}" class="byline-photo" />
        <div class="byline-text">
            <div class="byline-name">Gudibandi Madhava</div>
            <div class="byline-meta">Roll No: 25WU0203012 &middot; MBA-FS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    st.caption("Submitted by Gudibandi Madhava | Roll No: 25WU0203012 | MBA-FS")

# Placeholder for the executive insight banner -- filled in further down,
# once the current filter selection has been applied to the data, but it
# renders here at the top so it's the first thing a reader sees.
insight_banner = st.empty()

# =========================================================
# FILTER BAR -- a panel under the title, not a sidebar.
# Keeps filters visually attached to the content they control.
# =========================================================
st.markdown('<div class="filter-bar-label">FILTERS</div>', unsafe_allow_html=True)
with st.container(border=True):
    fc1, fc2, fc3 = st.columns(3)
    claim_types = sorted(indicators["claim_type"].dropna().unique())
    with fc1:
        selected_types = st.multiselect(
            "Claim type", claim_types, default=claim_types
        )
    channels = sorted(indicators["channel"].dropna().unique())
    with fc2:
        selected_channels = st.multiselect(
            "Channel", channels, default=channels
        )
    review_statuses = sorted(indicators["review_status"].dropna().unique())
    with fc3:
        selected_statuses = st.multiselect(
            "Review status", review_statuses, default=review_statuses
        )

    months = sorted(indicators["claim_month"].dropna().unique())
    selected_months = st.select_slider(
        "Claim month range",
        options=months,
        value=(months[0], months[-1]),
    )
st.write("")

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

# ---------------------------------------------------------
# Executive insight -- the one finding worth leading with:
# how much of the fraud-flagged book is missed by the
# separate rule-based indicator pipeline (recomputed live
# for whatever filters are currently applied).
# ---------------------------------------------------------
flagged_ids = set(f_claims.loc[f_claims["fraud_flag"] == 1, "claim_id"])
indicator_ids = set(f_indicators["claim_id"])
overlap_n = len(flagged_ids & indicator_ids)
gap_pct = (100 - (overlap_n / len(flagged_ids) * 100)) if flagged_ids else 0

insight_banner.markdown(f"""
<div class="insight-banner">
    <div class="insight-number">{gap_pct:.0f}%</div>
    <div class="insight-text">
        of fraud-flagged claims in the current view have <b>no matching fraud-indicator
        record</b>. The automated flag and the rule-based indicator pipeline are largely
        catching different claims.
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# TABS -- Overview / Trends & Drivers / Review Pipeline / Drill-down
# Replaces one long scroll: each tab loads instantly, no scrolling
# needed to reach a section.
# =========================================================
tab_overview, tab_trends, tab_pipeline, tab_drilldown = st.tabs(
    ["📊 Overview", "📈 Trends & Drivers", "🔎 Review Pipeline", "🗂️ Drill-down"]
)

with tab_overview:
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

# =========================================================
# TRENDS & DRIVERS TAB
# =========================================================
with tab_trends:
    col1, col2 = st.columns(2)

with tab_trends:
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
        st.plotly_chart(add_depth(fig1), width='stretch')
        st.caption("Takeaway: shows whether fraud activity is rising, falling, or seasonal.")

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
        fig2.add_hline(
            y=fraud_flag_rate, line_dash="dash", line_color=SLATE, line_width=1.5,
            annotation_text=f"Book average: {fraud_flag_rate:.1f}%",
            annotation_position="top left",
            annotation_font=dict(color=SLATE, size=12),
        )
        st.plotly_chart(add_depth(fig2), width='stretch')
        st.caption("Takeaway: identifies which claim types carry the highest fraud risk, relative to the book average.")

    col3, col4 = st.columns(2)

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
        st.plotly_chart(add_depth(fig3), width='stretch')
        st.caption("Takeaway: shows which fraud signal fires most, and how severe it tends to be.")

    with col4:
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
        fig5.add_hline(
            y=fraud_flag_rate, line_dash="dash", line_color=SLATE, line_width=1.5,
            annotation_text=f"Book average: {fraud_flag_rate:.1f}%",
            annotation_position="top left",
            annotation_font=dict(color=SLATE, size=12),
        )
        st.plotly_chart(add_depth(fig5), width='stretch')
        st.caption("Takeaway: shows whether certain acquisition channels bring in riskier business, relative to the book average.")

# =========================================================
# REVIEW PIPELINE TAB
# =========================================================
with tab_pipeline:
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
    fig_col, _ = st.columns([2, 1])
    with fig_col:
        st.plotly_chart(add_depth(fig4), width='stretch')
    st.caption("Takeaway: shows where cases are piling up in the review process. "
               "amber stages are still open, red is confirmed fraud, green is cleared.")

# =========================================================
# DRILL-DOWN TAB -- pick a claim type to see underlying records
# =========================================================
with tab_drilldown:
    st.subheader("Underlying records")
    drill_type = st.selectbox("Choose a claim type to inspect", claim_types)
    drill_df = f_indicators[f_indicators["claim_type"] == drill_type][
        ["claim_id", "indicator_type", "score", "review_status",
         "claim_amount", "status", "channel", "claim_month"]
    ].sort_values("score", ascending=False)
    st.dataframe(drill_df, width='stretch')
    st.caption(
        f"Showing {len(drill_df)} fraud-indicator records for claim type "
        f"'{drill_type}', sorted by risk score (highest first)."
    )

# =========================================================
# BACK TO TOP -- floating button, always in view
# =========================================================
st.markdown(
    '<a href="#top" class="back-to-top" title="Back to top">↑</a>',
    unsafe_allow_html=True,
)
