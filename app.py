import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sugar Trap · Market Gap Analysis",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Mono', monospace;
}

h1, h2, h3, h4 {
    font-family: 'Syne', sans-serif !important;
}

/* Main background */
.stApp {
    background-color: #0d0d0d;
    color: #f0ede6;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #141414;
    border-right: 1px solid #2a2a2a;
}

[data-testid="stSidebar"] * {
    color: #f0ede6 !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    padding: 16px !important;
}

[data-testid="stMetricLabel"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #888 !important;
}

[data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    color: #f0ede6 !important;
}

[data-testid="stMetricDelta"] {
    font-family: 'DM Mono', monospace !important;
}

/* Dividers */
hr {
    border-color: #2a2a2a !important;
}

/* Tabs */
[data-testid="stTabs"] button {
    font-family: 'DM Mono', monospace !important;
    font-size: 12px !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #888 !important;
}

[data-testid="stTabs"] button[aria-selected="true"] {
    color: #f0ede6 !important;
    border-bottom: 2px solid #e8ff47 !important;
}

/* Selectbox & sliders */
[data-testid="stSelectbox"] > div,
[data-testid="stMultiSelect"] > div {
    background: #1a1a1a !important;
    border-color: #2a2a2a !important;
}

/* Insight box */
.insight-box {
    background: linear-gradient(135deg, #1a1a1a 0%, #111 100%);
    border: 1px solid #e8ff47;
    border-left: 4px solid #e8ff47;
    border-radius: 4px;
    padding: 20px 24px;
    margin: 16px 0;
}

.insight-box h4 {
    color: #e8ff47 !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 8px;
}

.insight-box p {
    color: #f0ede6;
    font-size: 14px;
    line-height: 1.7;
    margin: 0;
}

.insight-box strong {
    color: #e8ff47;
}

/* Section label */
.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: #555;
    margin-bottom: 4px;
}

/* Plotly chart background overrides */
.js-plotly-plot .plotly .bg {
    fill: #0d0d0d !important;
}

/* Badge */
.badge {
    display: inline-block;
    background: #e8ff47;
    color: #0d0d0d;
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 2px;
    margin-left: 8px;
    vertical-align: middle;
}

/* Header strip */
.header-strip {
    background: #e8ff47;
    color: #0d0d0d;
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 6px 16px;
    border-radius: 2px;
    margin-bottom: 24px;
    display: inline-block;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
SUGAR_THRESHOLD  = 20   # g per 100g
PROTEIN_THRESHOLD = 10  # g per 100g

CATEGORY_COLORS = {
    "Beverages":           "#4e79a7",
    "Dairy":               "#59a14f",
    "Sweets":              "#f28e2b",
    "Meat & Seafood":      "#e15759",
    "Snacks":              "#76b7b2",
    "Condiments & Sauces": "#edc948",
    "Fruits & Vegetables": "#b07aa1",
    "Cereals & Grains":    "#ff9da7",
    "Other":               "#9c755f",
}

PLOT_THEME = dict(
    paper_bgcolor="#0d0d0d",
    plot_bgcolor="#141414",
    font_color="#f0ede6",
    font_family="DM Mono, monospace",
    gridcolor="#2a2a2a",
    zerolinecolor="#2a2a2a",
)

# ── Data loader ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    """Load dashboard_data.csv — expected alongside app.py."""
    try:
        df = pd.read_csv("dashboard_data.csv")
    except FileNotFoundError:
        st.error(
            "⚠️  `dashboard_data.csv` not found. "
            "Run the notebook first to export it, then place it in the same folder as app.py."
        )
        st.stop()

    # Derived columns
    df["blue_ocean"] = (
        (df["sugars_100g"]   <= SUGAR_THRESHOLD) &
        (df["proteins_100g"] >= PROTEIN_THRESHOLD)
    )
    df["quadrant"] = np.select(
        [
            (df["sugars_100g"] <= SUGAR_THRESHOLD) & (df["proteins_100g"] >= PROTEIN_THRESHOLD),
            (df["sugars_100g"] >  SUGAR_THRESHOLD) & (df["proteins_100g"] >= PROTEIN_THRESHOLD),
            (df["sugars_100g"] <= SUGAR_THRESHOLD) & (df["proteins_100g"] <  PROTEIN_THRESHOLD),
            (df["sugars_100g"] >  SUGAR_THRESHOLD) & (df["proteins_100g"] <  PROTEIN_THRESHOLD),
        ],
        ["High Protein · Low Sugar ✦", "High Protein · High Sugar", "Low Protein · Low Sugar", "Low Protein · High Sugar"],
        default="Unknown"
    )
    return df

df = load_data()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="section-label">Sugar Trap Analysis</p>', unsafe_allow_html=True)
    st.markdown("## Filters")
    st.markdown("---")

    all_cats = sorted([c for c in df["primary_category"].unique() if c != "Other"])
    selected_cats = st.multiselect(
        "Categories",
        options=all_cats,
        default=all_cats,
        help="Select one or more product categories to explore."
    )

    st.markdown("---")
    sugar_range = st.slider(
        "Sugar (g / 100g)",
        min_value=0, max_value=100,
        value=(0, 100), step=1
    )
    protein_range = st.slider(
        "Protein (g / 100g)",
        min_value=0, max_value=100,
        value=(0, 100), step=1
    )

    st.markdown("---")
    show_bo_only = st.checkbox("Blue Ocean products only", value=False)

    st.markdown("---")
    st.markdown(
        '<p class="section-label">Thresholds</p>'
        f'<p style="font-size:12px;color:#888;">Sugar ≤ {SUGAR_THRESHOLD}g &nbsp;|&nbsp; Protein ≥ {PROTEIN_THRESHOLD}g</p>',
        unsafe_allow_html=True
    )

# ── Filter data ────────────────────────────────────────────────────────────────
mask = (
    df["primary_category"].isin(selected_cats) &
    df["sugars_100g"].between(*sugar_range) &
    df["proteins_100g"].between(*protein_range)
)
if show_bo_only:
    mask &= df["blue_ocean"]

fdf = df[mask].copy()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="header-strip">Helix CPG Partners · Confidential</div>', unsafe_allow_html=True)
st.markdown("# Sugar Trap")
st.markdown("### Market Gap Analysis — Open Food Facts Dataset")
st.markdown("---")

# ── KPI row ────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
total_products   = len(fdf)
bo_products      = fdf["blue_ocean"].sum()
bo_pct           = (bo_products / total_products * 100) if total_products else 0
avg_sugar        = fdf["sugars_100g"].mean()
avg_protein      = fdf["proteins_100g"].mean()

k1.metric("Products (filtered)",   f"{total_products:,}")
k2.metric("Blue Ocean products",   f"{bo_products:,}")
k3.metric("Blue Ocean %",          f"{bo_pct:.1f}%")
k4.metric("Avg sugar (g/100g)",    f"{avg_sugar:.1f}g")
k5.metric("Avg protein (g/100g)",  f"{avg_protein:.1f}g")

st.markdown("---")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "01 · Nutrient Matrix",
    "02 · Category Breakdown",
    "03 · NutriScore Analysis",
    "04 · Protein Sources",
])

# ════════════════════════════════════════════════════════
# TAB 1 — Nutrient Matrix
# ════════════════════════════════════════════════════════
with tab1:
    st.markdown("#### Nutrient Matrix — Sugar vs Protein by Category")
    st.markdown(
        '<p style="font-size:12px;color:#888;margin-bottom:16px;">'
        'The shaded green quadrant (High Protein + Low Sugar) represents the Blue Ocean — '
        'products with ≥10g protein and ≤20g sugar per 100g.'
        '</p>',
        unsafe_allow_html=True
    )

    # Sample for performance
    plot_df = fdf.sample(min(len(fdf), 8000), random_state=42) if len(fdf) > 8000 else fdf

    fig = go.Figure()

    # Blue Ocean shading
    fig.add_shape(
        type="rect",
        x0=0, x1=SUGAR_THRESHOLD,
        y0=PROTEIN_THRESHOLD, y1=100,
        fillcolor="rgba(232,255,71,0.06)",
        line=dict(color="rgba(232,255,71,0.3)", width=1, dash="dot"),
        layer="below"
    )
    fig.add_annotation(
        x=2, y=97,
        text="✦ Blue Ocean",
        showarrow=False,
        font=dict(color="#e8ff47", size=11, family="DM Mono"),
        xanchor="left"
    )

    # Threshold lines
    fig.add_vline(x=SUGAR_THRESHOLD,   line_dash="dash", line_color="#444", line_width=1)
    fig.add_hline(y=PROTEIN_THRESHOLD, line_dash="dash", line_color="#444", line_width=1)

    # Scatter per category
    for cat in selected_cats:
        sub = plot_df[plot_df["primary_category"] == cat]
        if sub.empty:
            continue
        color = CATEGORY_COLORS.get(cat, "#888")
        fig.add_trace(go.Scatter(
            x=sub["sugars_100g"],
            y=sub["proteins_100g"],
            mode="markers",
            name=cat,
            marker=dict(
                color=color,
                size=5,
                opacity=0.45,
                line=dict(width=0),
            ),
            customdata=sub[["product_name", "brands", "blue_ocean"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Brand: %{customdata[1]}<br>"
                "Sugar: %{x:.1f}g | Protein: %{y:.1f}g<br>"
                "<extra>%{fullData.name}</extra>"
            )
        ))

    fig.update_layout(
        **PLOT_THEME,
        height=520,
        xaxis=dict(title="Sugar (g per 100g)", gridcolor="#2a2a2a", range=[0, 85]),
        yaxis=dict(title="Protein (g per 100g)", gridcolor="#2a2a2a", range=[0, 100]),
        legend=dict(
            bgcolor="#141414", bordercolor="#2a2a2a", borderwidth=1,
            font=dict(size=11)
        ),
        margin=dict(l=60, r=20, t=20, b=60),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Key Insight box
    st.markdown("""
    <div class="insight-box">
        <h4>⬡ Key Insight</h4>
        <p>
        Based on the data, the biggest market opportunity is in <strong>Fruits & Vegetables</strong>,
        specifically targeting products with <strong>17g of protein</strong> and less than
        <strong>5g of sugar</strong> per 100g.<br><br>
        Only <strong>2.9%</strong> of the 889 products in this category currently sit in the
        High-Protein / Low-Sugar quadrant — a clear Blue Ocean with virtually no competition.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# TAB 2 — Category Breakdown
# ════════════════════════════════════════════════════════
with tab2:
    st.markdown("#### Blue Ocean Penetration by Category")
    st.markdown(
        '<p style="font-size:12px;color:#888;margin-bottom:16px;">'
        'Percentage of products per category that fall in the High Protein / Low Sugar quadrant.'
        '</p>',
        unsafe_allow_html=True
    )

    gap = (
        fdf.groupby("primary_category")["blue_ocean"]
        .agg(["sum", "count"])
        .rename(columns={"sum": "bo_count", "count": "total"})
    )
    gap["bo_pct"] = (gap["bo_count"] / gap["total"] * 100).round(1)
    gap = gap.sort_values("bo_pct", ascending=True).reset_index()
    gap["color"] = gap["primary_category"].map(CATEGORY_COLORS).fillna("#888")

    col_a, col_b = st.columns([3, 2])

    with col_a:
        fig2 = go.Figure(go.Bar(
            x=gap["bo_pct"],
            y=gap["primary_category"],
            orientation="h",
            marker=dict(color=gap["color"], opacity=0.85),
            customdata=gap[["bo_count", "total"]].values,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Blue Ocean: %{x:.1f}%<br>"
                "%{customdata[0]:,} of %{customdata[1]:,} products<extra></extra>"
            )
        ))
        fig2.add_vline(
            x=gap["bo_pct"].mean(),
            line_dash="dash", line_color="#e8ff47", line_width=1,
            annotation_text=f"avg {gap['bo_pct'].mean():.1f}%",
            annotation_font=dict(color="#e8ff47", size=10),
        )
        fig2.update_layout(
            **PLOT_THEME,
            height=380,
            xaxis=dict(title="Blue Ocean %", gridcolor="#2a2a2a", ticksuffix="%"),
            yaxis=dict(gridcolor="#2a2a2a"),
            margin=dict(l=10, r=20, t=20, b=40),
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        st.markdown("##### Category Stats")
        display_gap = gap[["primary_category", "total", "bo_count", "bo_pct"]].sort_values("bo_pct", ascending=False)
        display_gap.columns = ["Category", "Total", "Blue Ocean", "BO %"]
        st.dataframe(
            display_gap.style.format({"BO %": "{:.1f}%", "Total": "{:,}", "Blue Ocean": "{:,}"}),
            hide_index=True,
            height=360,
            use_container_width=True,
        )

    # Per-category facet scatter
    st.markdown("---")
    st.markdown("#### Per-Category Scatter — Blue Ocean Highlighted")

    cats_to_plot = [c for c in gap["primary_category"].tolist() if c in selected_cats]
    n_cols = 4
    n_rows = int(np.ceil(len(cats_to_plot) / n_cols))

    if cats_to_plot:
        fig3 = make_subplots(
            rows=n_rows, cols=n_cols,
            subplot_titles=cats_to_plot,
            shared_xaxes=True, shared_yaxes=True,
            horizontal_spacing=0.04, vertical_spacing=0.1,
        )
        for i, cat in enumerate(cats_to_plot):
            r, c = divmod(i, n_cols)
            sub = fdf[fdf["primary_category"] == cat].sample(min(1500, len(fdf[fdf["primary_category"] == cat])), random_state=42)
            bo_pct_cat = gap.loc[gap["primary_category"] == cat, "bo_pct"].values
            bo_pct_val = bo_pct_cat[0] if len(bo_pct_cat) else 0

            fig3.add_trace(go.Scatter(
                x=sub["sugars_100g"], y=sub["proteins_100g"],
                mode="markers",
                marker=dict(
                    color=sub["blue_ocean"].map({True: "#e8ff47", False: "#3a3a3a"}),
                    size=4, opacity=0.6, line=dict(width=0)
                ),
                name=cat, showlegend=False,
                hovertemplate="Sugar: %{x:.1f}g | Protein: %{y:.1f}g<extra>" + cat + "</extra>"
            ), row=r+1, col=c+1)

            fig3.add_shape(
                type="rect", x0=0, x1=SUGAR_THRESHOLD,
                y0=PROTEIN_THRESHOLD, y1=100,
                fillcolor="rgba(232,255,71,0.06)",
                line=dict(color="rgba(232,255,71,0.25)", width=0.8),
                row=r+1, col=c+1
            )

        fig3.update_layout(
            **PLOT_THEME,
            height=n_rows * 200,
            margin=dict(l=40, r=10, t=40, b=40),
        )
        fig3.update_xaxes(gridcolor="#2a2a2a", range=[0, 85])
        fig3.update_yaxes(gridcolor="#2a2a2a", range=[0, 100])
        st.plotly_chart(fig3, use_container_width=True)


# ════════════════════════════════════════════════════════
# TAB 3 — NutriScore Analysis  (Candidate's Choice)
# ════════════════════════════════════════════════════════
with tab3:
    st.markdown("#### NutriScore Grade Distribution by Category")
    st.markdown(
        '<p style="font-size:12px;color:#888;margin-bottom:4px;">'
        "<b>Candidate's Choice addition.</b> NutriScore (A–E) is the EU's front-of-pack "
        "health label. Categories dominated by D/E grades present the biggest on-shelf "
        "reformulation opportunity for a healthier product."
        '</p>',
        unsafe_allow_html=True
    )

    if "nutriscore_grade" not in fdf.columns:
        st.info("nutriscore_grade column not found in dashboard_data.csv — re-export from the notebook with this column included.")
    else:
        SCORE_MAP   = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
        NS_COLORS   = {"a": "#2d9e2d", "b": "#85bb2f", "c": "#fecb02", "d": "#ee8100", "e": "#cc1900"}
        grade_order = ["a", "b", "c", "d", "e"]

        scored = fdf[fdf["nutriscore_grade"].isin(SCORE_MAP.keys())].copy()
        scored["ns_num"] = scored["nutriscore_grade"].map(SCORE_MAP)

        ns_by_cat = (
            scored.groupby("primary_category")["ns_num"]
            .mean().round(2).sort_values(ascending=False)
            .reset_index().rename(columns={"ns_num": "avg_score"})
        )

        grade_dist = (
            pd.crosstab(
                scored["primary_category"],
                scored["nutriscore_grade"],
                normalize="index"
            ) * 100
        )
        grade_dist = grade_dist.reindex(columns=[g for g in grade_order if g in grade_dist.columns])

        col1, col2 = st.columns([3, 2])

        with col1:
            fig4 = go.Figure()
            for grade in grade_order:
                if grade not in grade_dist.columns:
                    continue
                fig4.add_trace(go.Bar(
                    y=grade_dist.index,
                    x=grade_dist[grade],
                    name=f"Grade {grade.upper()}",
                    orientation="h",
                    marker_color=NS_COLORS[grade],
                    hovertemplate=f"Grade {grade.upper()}: %{{x:.1f}}%<extra>%{{y}}</extra>"
                ))
            fig4.update_layout(
                **PLOT_THEME,
                barmode="stack",
                height=380,
                xaxis=dict(title="% of products", ticksuffix="%", gridcolor="#2a2a2a"),
                yaxis=dict(gridcolor="#2a2a2a"),
                legend=dict(bgcolor="#141414", bordercolor="#2a2a2a", borderwidth=1, font=dict(size=11)),
                margin=dict(l=10, r=10, t=10, b=40),
            )
            st.plotly_chart(fig4, use_container_width=True)

        with col2:
            st.markdown("##### Avg NutriScore (1=A, 5=E)")
            fig5 = go.Figure(go.Bar(
                x=ns_by_cat["avg_score"],
                y=ns_by_cat["primary_category"],
                orientation="h",
                marker=dict(
                    color=ns_by_cat["avg_score"],
                    colorscale=[[0, "#2d9e2d"], [0.5, "#fecb02"], [1, "#cc1900"]],
                    cmin=1, cmax=5
                ),
                hovertemplate="<b>%{y}</b><br>Avg NutriScore: %{x:.2f}<extra></extra>"
            ))
            fig5.update_layout(
                **PLOT_THEME,
                height=380,
                xaxis=dict(title="Avg score (1=A, 5=E)", gridcolor="#2a2a2a", range=[1, 5]),
                yaxis=dict(gridcolor="#2a2a2a"),
                showlegend=False,
                margin=dict(l=10, r=10, t=10, b=40),
            )
            st.plotly_chart(fig5, use_container_width=True)

        worst = ns_by_cat.iloc[0]["primary_category"]
        st.markdown(f"""
        <div class="insight-box">
            <h4>⬡ Candidate's Choice Insight</h4>
            <p>
            <strong>{worst}</strong> has the worst average NutriScore across all categories.
            Launching a NutriScore A or B product in this space would provide a significant
            on-shelf competitive advantage — especially in EU markets where NutriScore
            labelling directly influences purchasing decisions.
            </p>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# TAB 4 — Protein Sources (Bonus Story 5)
# ════════════════════════════════════════════════════════
with tab4:
    st.markdown("#### Top Protein-Source Ingredients in Blue Ocean Products")
    st.markdown(
        '<p style="font-size:12px;color:#888;margin-bottom:16px;">'
        'Keyword analysis of <code>ingredients_text</code> across all High-Protein / Low-Sugar products.'
        '</p>',
        unsafe_allow_html=True
    )

    PROTEIN_KEYWORDS = [
        "whey", "casein", "soy", "pea protein", "egg", "chicken",
        "beef", "pork", "fish", "salmon", "tuna", "turkey",
        "milk", "lentil", "chickpea", "peanut", "almond",
        "oat", "hemp", "collagen", "gelatin", "tofu",
    ]

    if "ingredients_text" not in fdf.columns:
        st.info("ingredients_text column not found in dashboard_data.csv.")
    else:
        hp_df = fdf[fdf["blue_ocean"] & fdf["ingredients_text"].notna()].copy()

        counts = {}
        for kw in PROTEIN_KEYWORDS:
            counts[kw] = hp_df["ingredients_text"].str.lower().str.contains(kw, na=False).sum()

        protein_series = pd.Series(counts).sort_values(ascending=False)
        protein_series = protein_series[protein_series > 0].head(12)

        top3 = protein_series.head(3).index.tolist()

        col_p1, col_p2 = st.columns([3, 2])

        with col_p1:
            bar_colors = ["#e8ff47" if i < 3 else "#3a4a3a" for i in range(len(protein_series))]
            fig6 = go.Figure(go.Bar(
                y=protein_series.index,
                x=protein_series.values,
                orientation="h",
                marker=dict(color=bar_colors),
                hovertemplate="<b>%{y}</b><br>%{x:,} products<extra></extra>"
            ))
            fig6.update_layout(
                **PLOT_THEME,
                height=400,
                xaxis=dict(title="Blue Ocean products containing ingredient", gridcolor="#2a2a2a"),
                yaxis=dict(gridcolor="#2a2a2a"),
                showlegend=False,
                margin=dict(l=10, r=10, t=10, b=40),
            )
            st.plotly_chart(fig6, use_container_width=True)

        with col_p2:
            st.markdown("##### Top 3 Protein Sources")
            for i, src in enumerate(top3, 1):
                count = protein_series[src]
                st.markdown(f"""
                <div style="background:#1a1a1a;border:1px solid #2a2a2a;border-left:3px solid #e8ff47;
                            border-radius:4px;padding:12px 16px;margin-bottom:8px;">
                    <div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:0.1em;">#{i}</div>
                    <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:700;
                                color:#e8ff47;text-transform:capitalize;">{src}</div>
                    <div style="font-size:12px;color:#888;margin-top:2px;">{count:,} products</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("""
            <div class="insight-box" style="margin-top:16px;">
                <h4>⬡ R&D Recommendation</h4>
                <p>
                Formulate the new product around <strong>Soy</strong> and <strong>Oat</strong>
                as primary protein carriers — they dominate Blue Ocean products and carry strong
                plant-based consumer appeal with proven manufacturing scalability.
                </p>
            </div>
            """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="font-size:11px;color:#444;text-align:center;">'
    'Sugar Trap · Market Gap Analysis · Helix CPG Partners · '
    'Data: Open Food Facts (openfoodfacts.org) · CC BY-SA 4.0'
    '</p>',
    unsafe_allow_html=True
)
