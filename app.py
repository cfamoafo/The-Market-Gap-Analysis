import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sugar Trap Analysis",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme / CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #0f1117; }
    [data-testid="stSidebar"] { background: #16181f; border-right: 1px solid #2a2d3a; }
    [data-testid="stSidebar"] .stMarkdown p { color: #8b8fa8; font-size: 0.8rem; text-transform: uppercase; letter-spacing: .08em; }
    .metric-card {
        background: #16181f;
        border: 1px solid #2a2d3a;
        border-radius: 10px;
        padding: 20px 24px;
        text-align: center;
    }
    .metric-card .value { font-size: 2rem; font-weight: 700; color: #e2e8f0; }
    .metric-card .label { font-size: 0.78rem; color: #8b8fa8; text-transform: uppercase; letter-spacing: .06em; margin-top: 4px; }
    .metric-card .delta { font-size: 0.85rem; margin-top: 6px; }
    .section-header {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: .12em;
        color: #6ee7b7;
        margin: 32px 0 10px;
        border-bottom: 1px solid #2a2d3a;
        padding-bottom: 6px;
    }
    h1 { color: #e2e8f0 !important; }
    h2, h3 { color: #cbd5e0 !important; }
    p, li { color: #a0aec0; }
    .stMultiSelect span[data-baseweb="tag"] { background: #1e3a5f !important; }
    .insight-box {
        background: #0d2137;
        border-left: 3px solid #6ee7b7;
        border-radius: 0 8px 8px 0;
        padding: 14px 18px;
        margin: 10px 0 20px;
        color: #cbd5e0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Constants ────────────────────────────────────────────────────────────────
SUGAR_THRESHOLD = 20
PROTEIN_THRESHOLD = 10
NUTRISCORE_ORDER = ["a", "b", "c", "d", "e"]
NUTRISCORE_COLORS = {"a": "#2d9e2d", "b": "#85bb2f", "c": "#fecb02", "d": "#ee8100", "e": "#cc3300"}
CATEGORY_COLORS = px.colors.qualitative.Safe

# ── Data loading ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("dashboard_data.csv")
    ps = pd.read_csv("protein_sources.csv", index_col=0)
    df["blue_ocean"] = (df["sugars_100g"] <= SUGAR_THRESHOLD) & (df["proteins_100g"] >= PROTEIN_THRESHOLD)
    df["nutriscore_grade"] = df["nutriscore_grade"].str.lower()
    return df, ps

try:
    df_full, protein_sources = load_data()
except FileNotFoundError:
    st.error("Place `dashboard_data.csv` and `protein_sources.csv` in the same folder as this script.")
    st.stop()

# ── Sidebar filters ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 Sugar Trap")
    st.markdown("Market Gap Analysis")
    st.divider()

    st.markdown("**Categories**")
    all_cats = sorted(df_full["primary_category"].unique())
    selected_cats = st.multiselect("", all_cats, default=all_cats, label_visibility="collapsed")

    st.markdown("**NutriScore grades**")
    valid_grades = [g for g in NUTRISCORE_ORDER if g in df_full["nutriscore_grade"].unique()]
    selected_grades = st.multiselect("", NUTRISCORE_ORDER, default=valid_grades, label_visibility="collapsed")

    st.divider()
    st.markdown("**Blue Ocean thresholds**")
    sugar_thresh = st.slider("Max sugar (g/100g)", 0, 50, SUGAR_THRESHOLD)
    protein_thresh = st.slider("Min protein (g/100g)", 0, 30, PROTEIN_THRESHOLD)
    st.divider()
    st.markdown("Data source: Open Food Facts · 500k products sampled · Cleaned to 42,345 rows")

# ── Filter data ──────────────────────────────────────────────────────────────
df = df_full[df_full["primary_category"].isin(selected_cats)].copy()
df["blue_ocean"] = (df["sugars_100g"] <= sugar_thresh) & (df["proteins_100g"] >= protein_thresh)

# ── Header ───────────────────────────────────────────────────────────────────
st.title("Sugar Trap — Market Gap Analysis")
st.markdown("Identifying **High-Protein / Low-Sugar** white spaces across packaged food categories.")

# ── KPI row ──────────────────────────────────────────────────────────────────
total = len(df)
bo_count = df["blue_ocean"].sum()
bo_pct = bo_count / total * 100 if total else 0
avg_sugar = df["sugars_100g"].mean()
avg_protein = df["proteins_100g"].mean()

c1, c2, c3, c4 = st.columns(4)
for col, val, lbl, delta in zip(
    [c1, c2, c3, c4],
    [f"{total:,}", f"{bo_count:,}", f"{bo_pct:.1f}%", f"{avg_sugar:.1f}g"],
    ["Products", "Blue Ocean", "BO penetration", "Avg sugar /100g"],
    ["", f"<span style='color:#6ee7b7'>≤{sugar_thresh}g sugar · ≥{protein_thresh}g protein</span>",
     "<span style='color:#f6ad55'>market gap opportunity</span>",
     f"<span style='color:#fc8181'>avg protein: {avg_protein:.1f}g</span>"]
):
    col.markdown(f"""<div class="metric-card">
        <div class="value">{val}</div>
        <div class="label">{lbl}</div>
        <div class="delta">{delta}</div>
    </div>""", unsafe_allow_html=True)

# ── Tab layout ───────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🗺 Nutrient Matrix", "📊 Category Breakdown", "🧬 Protein Sources", "🏷 NutriScore Gap"])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — Nutrient Matrix scatter
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<p class="section-header">Sugar vs Protein — Blue Ocean Quadrant</p>', unsafe_allow_html=True)

    st.markdown(f"""<div class="insight-box">
        The <strong>shaded green zone</strong> (sugar ≤ {sugar_thresh}g · protein ≥ {protein_thresh}g per 100g) is the Blue Ocean quadrant —
        high-protein, low-sugar products where competition is thin. Dots inside this zone are market-gap candidates.
    </div>""", unsafe_allow_html=True)

    sample = df.sample(min(8000, len(df)), random_state=42)

    fig = px.scatter(
        sample,
        x="sugars_100g",
        y="proteins_100g",
        color="primary_category",
        hover_data=["product_name", "brands"],
        opacity=0.45,
        color_discrete_sequence=CATEGORY_COLORS,
        labels={"sugars_100g": "Sugar (g / 100g)", "proteins_100g": "Protein (g / 100g)", "primary_category": "Category"},
        height=520,
    )

    # Blue ocean shading
    fig.add_shape(type="rect", x0=0, x1=sugar_thresh, y0=protein_thresh, y1=df["proteins_100g"].max() + 2,
                  fillcolor="rgba(110,231,183,0.10)", line=dict(width=0))
    # Threshold lines
    fig.add_vline(x=sugar_thresh, line_dash="dash", line_color="#6ee7b7", line_width=1)
    fig.add_hline(y=protein_thresh, line_dash="dash", line_color="#6ee7b7", line_width=1)

    fig.add_annotation(x=sugar_thresh / 2, y=df["proteins_100g"].max(),
                       text="🌊 Blue Ocean", showarrow=False,
                       font=dict(color="#6ee7b7", size=12))

    fig.update_layout(
        paper_bgcolor="#0f1117", plot_bgcolor="#16181f",
        font_color="#a0aec0", legend_title_text="Category",
        xaxis=dict(gridcolor="#2a2d3a", zerolinecolor="#2a2d3a"),
        yaxis=dict(gridcolor="#2a2d3a", zerolinecolor="#2a2d3a"),
        margin=dict(t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — Category breakdown
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<p class="section-header">Blue Ocean penetration by category</p>', unsafe_allow_html=True)

    gap = (
        df.groupby("primary_category")["blue_ocean"]
        .agg(["sum", "count"])
        .rename(columns={"sum": "blue_ocean_count", "count": "total"})
    )
    gap["blue_ocean_pct"] = (gap["blue_ocean_count"] / gap["total"] * 100).round(1)
    gap = gap[gap["total"] >= 10].sort_values("blue_ocean_pct")

    col_a, col_b = st.columns([2, 1])

    with col_a:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            y=gap.index,
            x=gap["blue_ocean_pct"],
            orientation="h",
            marker_color=[CATEGORY_COLORS[i % len(CATEGORY_COLORS)] for i in range(len(gap))],
            text=[f"{v:.1f}%" for v in gap["blue_ocean_pct"]],
            textposition="outside",
            textfont=dict(color="#e2e8f0", size=11),
        ))
        fig2.update_layout(
            paper_bgcolor="#0f1117", plot_bgcolor="#16181f",
            font_color="#a0aec0", height=400,
            xaxis=dict(title="% products in Blue Ocean", gridcolor="#2a2d3a", ticksuffix="%"),
            yaxis=dict(gridcolor="#2a2d3a"),
            margin=dict(t=10, b=30, l=10, r=60),
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        st.markdown("**Category table**")
        display = gap.sort_values("blue_ocean_pct", ascending=False).reset_index()
        display.columns = ["Category", "BO Products", "Total", "BO %"]
        st.dataframe(
            display.style.background_gradient(subset=["BO %"], cmap="YlGn"),
            use_container_width=True, hide_index=True, height=390,
        )

    # Biggest opportunity (lowest BO% in large categories)
    opp = gap[gap["total"] >= 500].sort_values("blue_ocean_pct").iloc[0]
    st.markdown(f"""<div class="insight-box">
        <strong>Key Insight:</strong> <em>{opp.name}</em> has the lowest Blue Ocean penetration ({opp['blue_ocean_pct']:.1f}%) among categories
        with 500+ products — the clearest white space. Only {int(opp['blue_ocean_count'])} of {int(opp['total'])} products
        sit in the High-Protein / Low-Sugar quadrant.
    </div>""", unsafe_allow_html=True)

    # Per-category facet scatter
    st.markdown('<p class="section-header">Per-category nutrient distribution</p>', unsafe_allow_html=True)
    cats_to_plot = gap.sort_values("blue_ocean_pct", ascending=False).index.tolist()
    n_cols = 4
    n_rows = int(np.ceil(len(cats_to_plot) / n_cols))

    fig3 = make_subplots(rows=n_rows, cols=n_cols,
                         subplot_titles=[f"{c} ({gap.loc[c,'blue_ocean_pct']:.1f}% BO)" for c in cats_to_plot],
                         shared_xaxes=True, shared_yaxes=True,
                         horizontal_spacing=0.05, vertical_spacing=0.12)

    for idx, cat in enumerate(cats_to_plot):
        r, c_idx = divmod(idx, n_cols)
        sub = df[df["primary_category"] == cat].sample(min(500, len(df[df["primary_category"] == cat])), random_state=42)
        fig3.add_trace(go.Scatter(
            x=sub["sugars_100g"], y=sub["proteins_100g"],
            mode="markers",
            marker=dict(size=4, opacity=0.4, color=CATEGORY_COLORS[idx % len(CATEGORY_COLORS)]),
            showlegend=False,
        ), row=r + 1, col=c_idx + 1)
        fig3.add_shape(type="rect", x0=0, x1=sugar_thresh, y0=protein_thresh, y1=55,
                       fillcolor="rgba(110,231,183,0.12)", line=dict(width=0),
                       row=r + 1, col=c_idx + 1)

    fig3.update_layout(height=n_rows * 200, paper_bgcolor="#0f1117", plot_bgcolor="#16181f",
                       font_color="#a0aec0", margin=dict(t=30, b=10))
    fig3.update_xaxes(gridcolor="#2a2d3a", range=[0, 85])
    fig3.update_yaxes(gridcolor="#2a2d3a", range=[0, 55])
    st.plotly_chart(fig3, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — Protein sources
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<p class="section-header">Top protein-source ingredients in Blue Ocean products</p>', unsafe_allow_html=True)

    st.markdown("""<div class="insight-box">
        Ranked by how many High-Protein / Low-Sugar products list each ingredient. These are the formulation
        building blocks already proven to work in the Blue Ocean quadrant.
    </div>""", unsafe_allow_html=True)

    ps_df = protein_sources.reset_index()
    ps_df.columns = ["Ingredient", "Count"]
    ps_df = ps_df.sort_values("Count", ascending=True)

    fig4 = go.Figure(go.Bar(
        y=ps_df["Ingredient"],
        x=ps_df["Count"],
        orientation="h",
        marker=dict(
            color=ps_df["Count"],
            colorscale="Teal",
            showscale=False,
        ),
        text=ps_df["Count"].apply(lambda x: f"{x:,}"),
        textposition="outside",
        textfont=dict(color="#e2e8f0", size=11),
    ))
    fig4.update_layout(
        paper_bgcolor="#0f1117", plot_bgcolor="#16181f",
        font_color="#a0aec0", height=420,
        xaxis=dict(title="Blue Ocean products containing ingredient", gridcolor="#2a2d3a"),
        yaxis=dict(gridcolor="#2a2d3a"),
        margin=dict(t=10, b=30, r=60),
    )
    st.plotly_chart(fig4, use_container_width=True)

    top3 = ps_df.sort_values("Count", ascending=False).head(3)
    st.markdown(f"""<div class="insight-box">
        <strong>Top 3 Protein Sources:</strong>
        🥇 <strong>{top3.iloc[0]['Ingredient'].title()}</strong> ({top3.iloc[0]['Count']:,} products) &nbsp;·&nbsp;
        🥈 <strong>{top3.iloc[1]['Ingredient'].title()}</strong> ({top3.iloc[1]['Count']:,} products) &nbsp;·&nbsp;
        🥉 <strong>{top3.iloc[2]['Ingredient'].title()}</strong> ({top3.iloc[2]['Count']:,} products)
    </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — NutriScore gap
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<p class="section-header">NutriScore grade distribution by category</p>', unsafe_allow_html=True)

    st.markdown("""<div class="insight-box">
        NutriScore (A–E) is increasingly prominent on EU packaging. Categories dominated by D/E grades offer the
        biggest on-shelf advantage for a reformulated, higher-scoring product.
    </div>""", unsafe_allow_html=True)

    scored = df[df["nutriscore_grade"].isin(NUTRISCORE_ORDER)].copy()
    if scored.empty:
        st.warning("No valid NutriScore grades in the current filter selection.")
    else:
        grade_dist = pd.crosstab(
            scored["primary_category"],
            scored["nutriscore_grade"],
            normalize="index",
        ) * 100
        # Keep only grades that exist
        available_grades = [g for g in NUTRISCORE_ORDER if g in grade_dist.columns]
        grade_dist = grade_dist[available_grades]

        fig5 = go.Figure()
        for grade in available_grades:
            fig5.add_trace(go.Bar(
                name=f"NutriScore {grade.upper()}",
                y=grade_dist.index,
                x=grade_dist[grade],
                orientation="h",
                marker_color=NUTRISCORE_COLORS[grade],
                text=grade_dist[grade].apply(lambda v: f"{v:.0f}%" if v > 5 else ""),
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(color="white", size=10),
            ))

        fig5.update_layout(
            barmode="stack",
            paper_bgcolor="#0f1117", plot_bgcolor="#16181f",
            font_color="#a0aec0", height=420,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        title_text="NutriScore"),
            xaxis=dict(title="% of products", ticksuffix="%", gridcolor="#2a2d3a", range=[0, 100]),
            yaxis=dict(gridcolor="#2a2d3a"),
            margin=dict(t=40, b=30),
        )
        st.plotly_chart(fig5, use_container_width=True)

        # Average NutriScore numeric table
        SCORE_MAP = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
        scored["ns_num"] = scored["nutriscore_grade"].map(SCORE_MAP)
        ns_by_cat = (
            scored.groupby("primary_category")["ns_num"]
            .agg(["mean", "count"])
            .rename(columns={"mean": "Avg NutriScore", "count": "Scored products"})
            .sort_values("Avg NutriScore", ascending=False)
            .reset_index()
        )
        ns_by_cat["Avg NutriScore"] = ns_by_cat["Avg NutriScore"].round(2)
        ns_by_cat.columns = ["Category", "Avg NutriScore (1=A, 5=E)", "Scored Products"]

        worst = ns_by_cat.iloc[0]["Category"]
        st.markdown(f"""<div class="insight-box">
            <strong>Candidate's Choice:</strong> <em>{worst}</em> has the worst average NutriScore across all categories.
            Launching a NutriScore A/B reformulated product here offers the biggest competitive on-shelf advantage —
            especially in EU markets where NutriScore labelling influences purchase decisions.
        </div>""", unsafe_allow_html=True)

        col_ns1, col_ns2 = st.columns([1, 2])
        with col_ns1:
            st.dataframe(
                ns_by_cat.style.background_gradient(subset=["Avg NutriScore (1=A, 5=E)"], cmap="RdYlGn_r"),
                use_container_width=True, hide_index=True,
            )
        with col_ns2:
            # Grade A proportion per category
            if "a" in grade_dist.columns:
                a_share = grade_dist["a"].sort_values().reset_index()
                a_share.columns = ["Category", "Grade A %"]
                fig6 = px.bar(
                    a_share, x="Grade A %", y="Category", orientation="h",
                    color="Grade A %", color_continuous_scale="Greens",
                    labels={"Grade A %": "% with NutriScore A"},
                    title="Share of NutriScore A products by category",
                    height=370,
                )
                fig6.update_layout(
                    paper_bgcolor="#0f1117", plot_bgcolor="#16181f",
                    font_color="#a0aec0", coloraxis_showscale=False,
                    title_font=dict(size=13, color="#cbd5e0"),
                    xaxis=dict(gridcolor="#2a2d3a", ticksuffix="%"),
                    yaxis=dict(gridcolor="#2a2d3a"),
                    margin=dict(t=40, b=20),
                )
                st.plotly_chart(fig6, use_container_width=True)

# ── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center;color:#4a5568;font-size:0.75rem;'>Sugar Trap Analysis · Open Food Facts data · "
    "Blue Ocean = High Protein + Low Sugar quadrant</p>",
    unsafe_allow_html=True,
)
