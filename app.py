import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Sugar Trap · Market Gap Analysis",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"]          { font-family: 'DM Mono', monospace; }
h1, h2, h3, h4                      { font-family: 'Syne', sans-serif !important; }
.stApp                               { background-color: #0d0d0d; color: #f0ede6; }
[data-testid="stSidebar"]           { background-color: #141414; border-right: 1px solid #2a2a2a; }
[data-testid="stSidebar"] *         { color: #f0ede6 !important; }
[data-testid="stMetric"]            { background:#1a1a1a; border:1px solid #2a2a2a; border-radius:4px; padding:16px !important; }
[data-testid="stMetricLabel"]       { font-family:'DM Mono',monospace !important; font-size:11px !important; text-transform:uppercase; letter-spacing:.08em; color:#888 !important; }
[data-testid="stMetricValue"]       { font-family:'Syne',sans-serif !important; font-size:28px !important; font-weight:700 !important; color:#f0ede6 !important; }
hr                                   { border-color:#2a2a2a !important; }
[data-testid="stTabs"] button        { font-family:'DM Mono',monospace !important; font-size:12px !important; text-transform:uppercase; letter-spacing:.06em; color:#888 !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color:#f0ede6 !important; border-bottom:2px solid #e8ff47 !important; }
.insight-box { background:linear-gradient(135deg,#1a1a1a 0%,#111 100%); border:1px solid #e8ff47; border-left:4px solid #e8ff47; border-radius:4px; padding:20px 24px; margin:16px 0; }
.insight-box h4 { color:#e8ff47 !important; font-size:11px !important; text-transform:uppercase; letter-spacing:.12em; margin-bottom:8px; }
.insight-box p  { color:#f0ede6; font-size:14px; line-height:1.7; margin:0; }
.insight-box strong { color:#e8ff47; }
.header-strip { background:#e8ff47; color:#0d0d0d; font-family:'Syne',sans-serif; font-weight:800; font-size:11px; letter-spacing:.12em; text-transform:uppercase; padding:6px 16px; border-radius:2px; margin-bottom:24px; display:inline-block; }
.section-label { font-family:'DM Mono',monospace; font-size:10px; text-transform:uppercase; letter-spacing:.15em; color:#555; margin-bottom:4px; }
</style>
""", unsafe_allow_html=True)

# ── Constants (match notebook exactly) ────────────────────────────────────────
SUGAR_THRESHOLD   = 20
PROTEIN_THRESHOLD = 10

CATEGORY_MAP = {
    "Dairy":               ["dairy","cheese","yogurt","yoghurt","butter","cream"],
    "Meat & Seafood":      ["meat","chicken","beef","pork","fish","seafood"],
    "Sweets":              ["sweet","chocolate","candy","confection","biscuit"],
    "Snacks":              ["snack","chip","crisp","cracker","pretzel","popcorn"],
    "Beverages":           ["beverage","drink","juice","water","soda","tea","coffee"],
    "Cereals & Grains":    ["cereal","grain","bread","pasta","rice","flour"],
    "Fruits & Vegetables": ["fruit","vegetable","salad","legume","bean"],
    "Condiments & Sauces": ["sauce","condiment","dressing","mayonnaise","ketchup"],
}

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

NS_COLORS   = {"a":"#2d9e2d","b":"#85bb2f","c":"#fecb02","d":"#ee8100","e":"#cc1900"}
GRADE_ORDER = ["a","b","c","d","e"]
SCORE_MAP   = {"a":1,"b":2,"c":3,"d":4,"e":5}

PROTEIN_KEYWORDS = [
    "whey","casein","soy","pea protein","egg","chicken",
    "beef","pork","fish","salmon","tuna","turkey",
    "milk","lentil","chickpea","peanut","almond",
    "oat","hemp","collagen","gelatin","tofu",
]

PLOT_THEME = dict(
    paper_bgcolor="#0d0d0d",
    plot_bgcolor="#141414",
    font=dict(color="#f0ede6", family="DM Mono, monospace"),
)

# ── Data: mirrors notebook export exactly ──────────────────────────────────────
@st.cache_data(show_spinner="Loading data…")
def load_data():
    # Load from dashboard_data.csv if present (notebook export),
    # else build from food_sample.parquet using the same notebook logic.
    try:
        df = pd.read_csv("dashboard_data.csv")
        # dashboard_data.csv already has primary_category & nutriscore_grade
    except FileNotFoundError:
        raw = pd.read_parquet("food_sample.parquet")

        def assign_category(tags):
            if not isinstance(tags, str):
                return "Other"
            t = tags.lower()
            for cat, kws in CATEGORY_MAP.items():
                if any(k in t for k in kws):
                    return cat
            return "Other"

        raw["primary_category"] = raw["categories_tags"].apply(assign_category)
        raw["nutriscore_grade"]  = raw["nutrition_grade_fr"]

        EXPORT_COLS = [
            "product_name","brands","categories_tags","countries_en",
            "ingredients_text","nutriscore_grade","nova_group",
            "sugars_100g","proteins_100g","fat_100g","fiber_100g",
            "energy_100g","saturated-fat_100g","salt_100g",
            "carbohydrates_100g","primary_category",
        ]
        df = raw[raw["primary_category"] != "Other"][EXPORT_COLS].copy()

        # Story 1 clean-up (notebook order)
        df = df.dropna(subset=["product_name","sugars_100g","proteins_100g"])
        for col in ["sugars_100g","proteins_100g","fat_100g","fiber_100g",
                    "saturated-fat_100g","salt_100g","carbohydrates_100g"]:
            if col in df.columns:
                df = df[(df[col].isna()) | ((df[col] >= 0) & (df[col] <= 100))]
        if "energy_100g" in df.columns:
            df = df[(df["energy_100g"].isna()) | ((df["energy_100g"] >= 0) & (df["energy_100g"] <= 900))]
        # 99th-percentile cap (notebook)
        sugar_cutoff   = df["sugars_100g"].quantile(0.99)
        protein_cutoff = df["proteins_100g"].quantile(0.99)
        df = df[(df["sugars_100g"] <= sugar_cutoff) & (df["proteins_100g"] <= protein_cutoff)]

    df["blue_ocean"] = (
        (df["sugars_100g"]   <= SUGAR_THRESHOLD) &
        (df["proteins_100g"] >= PROTEIN_THRESHOLD)
    )
    df["quadrant"] = np.select(
        [
            (df["sugars_100g"] <= SUGAR_THRESHOLD) & (df["proteins_100g"] >= PROTEIN_THRESHOLD),
            (df["sugars_100g"] >  SUGAR_THRESHOLD) & (df["proteins_100g"] >= PROTEIN_THRESHOLD),
            (df["sugars_100g"] <= SUGAR_THRESHOLD) & (df["proteins_100g"] <  PROTEIN_THRESHOLD),
        ],
        ["High Protein · Low Sugar ✦","High Protein · High Sugar","Low Protein · Low Sugar"],
        default="Low Protein · High Sugar",
    )
    return df

df = load_data()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="section-label">Sugar Trap Analysis</p>', unsafe_allow_html=True)
    st.markdown("## Filters")
    st.markdown("---")

    all_cats = sorted(df["primary_category"].unique())
    selected_cats = st.multiselect("Categories", options=all_cats, default=all_cats)

    st.markdown("---")
    sugar_range   = st.slider("Sugar (g / 100g)",   0, 100, (0, 100), step=1)
    protein_range = st.slider("Protein (g / 100g)", 0, 100, (0, 100), step=1)

    st.markdown("---")
    show_bo_only = st.checkbox("Blue Ocean products only", value=False)

    st.markdown("---")
    st.markdown(
        '<p class="section-label">Thresholds</p>'
        f'<p style="font-size:12px;color:#888;">Sugar ≤ {SUGAR_THRESHOLD}g &nbsp;|&nbsp; Protein ≥ {PROTEIN_THRESHOLD}g</p>',
        unsafe_allow_html=True,
    )

# ── Filter ─────────────────────────────────────────────────────────────────────
mask = (
    df["primary_category"].isin(selected_cats) &
    df["sugars_100g"].between(*sugar_range) &
    df["proteins_100g"].between(*protein_range)
)
if show_bo_only:
    mask &= df["blue_ocean"]
fdf = df[mask].copy()

# ── Pre-compute aggregates ────────────────────────────────────────────────────
gap = (
    fdf.groupby("primary_category")["blue_ocean"]
    .agg(bo_count="sum", total="count")
    .assign(bo_pct=lambda x: (x["bo_count"] / x["total"] * 100).round(1))
    .sort_values("bo_pct", ascending=True)
    .reset_index()
)

# Recommendation: lowest BO % with total >= 500 (notebook logic)
opportunity = gap[gap["total"] >= 500].sort_values("bo_pct", ascending=True)
if not opportunity.empty:
    top         = opportunity.iloc[0]
    top_cat     = top["primary_category"]
    bo_subset   = fdf[(fdf["primary_category"] == top_cat) & fdf["blue_ocean"]]
    if len(bo_subset) > 5:
        target_protein = int(round(bo_subset["proteins_100g"].quantile(0.75)))
        target_sugar   = int(max(5, round(bo_subset["sugars_100g"].quantile(0.25))))
    else:
        target_protein = PROTEIN_THRESHOLD
        target_sugar   = SUGAR_THRESHOLD // 2
else:
    top_cat, target_protein, target_sugar = "N/A", PROTEIN_THRESHOLD, SUGAR_THRESHOLD // 2
    top = pd.Series({"bo_pct": 0, "total": 0})

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="header-strip">Helix CPG Partners · Confidential</div>', unsafe_allow_html=True)
st.markdown("# Sugar Trap")
st.markdown("### Market Gap Analysis — Open Food Facts Dataset")
st.markdown("---")

# ── KPIs ───────────────────────────────────────────────────────────────────────
total_products = len(fdf)
bo_products    = int(fdf["blue_ocean"].sum())
bo_pct_kpi     = (bo_products / total_products * 100) if total_products else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Products (filtered)",  f"{total_products:,}")
k2.metric("Blue Ocean products",  f"{bo_products:,}")
k3.metric("Blue Ocean %",         f"{bo_pct_kpi:.1f}%")
k4.metric("Avg sugar (g/100g)",   f"{fdf['sugars_100g'].mean():.1f}g")
k5.metric("Avg protein (g/100g)", f"{fdf['proteins_100g'].mean():.1f}g")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs([
    "01 · Nutrient Matrix",
    "02 · Category Breakdown",
    "03 · NutriScore Analysis",
    "04 · Protein Sources",
])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — Nutrient Matrix  (Story 3)
# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("#### Nutrient Matrix — Sugar vs Protein by Category")
    st.markdown(
        f'<p style="font-size:12px;color:#888;margin-bottom:16px;">'
        f'Shaded quadrant = Blue Ocean (protein ≥ {PROTEIN_THRESHOLD}g, sugar ≤ {SUGAR_THRESHOLD}g per 100g). '
        f'Non-Other categories only.</p>',
        unsafe_allow_html=True,
    )

    plot_df = fdf.sample(min(len(fdf), 8000), random_state=42) if len(fdf) > 8000 else fdf

    fig = go.Figure()
    fig.add_shape(
        type="rect", x0=0, x1=SUGAR_THRESHOLD, y0=PROTEIN_THRESHOLD, y1=100,
        fillcolor="rgba(232,255,71,0.06)",
        line=dict(color="rgba(232,255,71,0.3)", width=1, dash="dot"),
        layer="below",
    )
    fig.add_annotation(
        x=1, y=97, text="✦ Blue Ocean", showarrow=False,
        font=dict(color="#e8ff47", size=11, family="DM Mono"), xanchor="left",
    )
    fig.add_vline(x=SUGAR_THRESHOLD,   line_dash="dash", line_color="#444", line_width=1)
    fig.add_hline(y=PROTEIN_THRESHOLD, line_dash="dash", line_color="#444", line_width=1)

    for cat in selected_cats:
        sub = plot_df[plot_df["primary_category"] == cat]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["sugars_100g"], y=sub["proteins_100g"],
            mode="markers", name=cat,
            marker=dict(color=CATEGORY_COLORS.get(cat, "#888"), size=5, opacity=0.4, line=dict(width=0)),
            customdata=sub[["product_name","brands"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Brand: %{customdata[1]}<br>"
                "Sugar: %{x:.1f}g | Protein: %{y:.1f}g"
                "<extra>%{fullData.name}</extra>"
            ),
        ))

    fig.update_layout(
        **PLOT_THEME, height=520,
        xaxis=dict(title="Sugar (g per 100g)",   gridcolor="#2a2a2a", range=[0, 85]),
        yaxis=dict(title="Protein (g per 100g)", gridcolor="#2a2a2a", range=[0, 100]),
        legend=dict(bgcolor="#141414", bordercolor="#2a2a2a", borderwidth=1, font=dict(size=11)),
        margin=dict(l=60, r=20, t=20, b=60),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Story 4 insight box — fully data-driven
    st.markdown(f"""
    <div class="insight-box">
        <h4>⬡ Key Insight</h4>
        <p>
        Based on the data, the biggest market opportunity is in <strong>{top_cat}</strong>,
        specifically targeting products with <strong>{target_protein}g of protein</strong>
        and less than <strong>{target_sugar}g of sugar</strong> per 100g.<br><br>
        Only <strong>{top['bo_pct']:.1f}%</strong> of the {int(top['total']):,} products
        in this category currently sit in the High-Protein / Low-Sugar quadrant —
        a clear Blue Ocean with virtually no competition.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — Category Breakdown  (Story 2)
# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("#### Blue Ocean Penetration by Category")
    st.markdown(
        '<p style="font-size:12px;color:#888;margin-bottom:16px;">'
        "% of products per category that fall in the High Protein / Low Sugar quadrant."
        "</p>",
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns([3, 2])

    with col_a:
        fig2 = go.Figure(go.Bar(
            x=gap["bo_pct"],
            y=gap["primary_category"],
            orientation="h",
            marker=dict(color=[CATEGORY_COLORS.get(c, "#888") for c in gap["primary_category"]], opacity=0.85),
            customdata=gap[["bo_count","total"]].values,
            hovertemplate=(
                "<b>%{y}</b><br>Blue Ocean: %{x:.1f}%<br>"
                "%{customdata[0]:,} of %{customdata[1]:,} products<extra></extra>"
            ),
        ))
        avg_bo = gap["bo_pct"].mean()
        fig2.add_vline(
            x=avg_bo, line_dash="dash", line_color="#e8ff47", line_width=1,
            annotation_text=f"avg {avg_bo:.1f}%",
            annotation_font=dict(color="#e8ff47", size=10),
        )
        fig2.update_layout(
            **PLOT_THEME, height=380,
            xaxis=dict(title="Blue Ocean %", gridcolor="#2a2a2a", ticksuffix="%"),
            yaxis=dict(gridcolor="#2a2a2a"),
            margin=dict(l=10, r=20, t=20, b=40),
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        st.markdown("##### Category Stats")
        display_gap = (
            gap[["primary_category","total","bo_count","bo_pct"]]
            .sort_values("bo_pct", ascending=False)
            .rename(columns={"primary_category":"Category","total":"Total",
                              "bo_count":"Blue Ocean","bo_pct":"BO %"})
        )
        st.dataframe(
            display_gap.style.format({"BO %":"{:.1f}%","Total":"{:,}","Blue Ocean":"{:,}"}),
            hide_index=True, height=360, use_container_width=True,
        )

    # Faceted scatter per category
    st.markdown("---")
    st.markdown("#### Per-Category Scatter — Blue Ocean Highlighted")

    cats_to_plot = gap["primary_category"].tolist()
    n_cols = 4
    n_rows = int(np.ceil(len(cats_to_plot) / n_cols))

    if cats_to_plot:
        fig3 = make_subplots(
            rows=n_rows, cols=n_cols,
            subplot_titles=[f"{c} ({gap.loc[gap['primary_category']==c,'bo_pct'].values[0]:.1f}% BO)" for c in cats_to_plot],
            shared_xaxes=True, shared_yaxes=True,
            horizontal_spacing=0.04, vertical_spacing=0.12,
        )
        for i, cat in enumerate(cats_to_plot):
            r, c = divmod(i, n_cols)
            sub = fdf[fdf["primary_category"] == cat].sample(
                min(1500, int((fdf["primary_category"] == cat).sum())), random_state=42
            )
            fig3.add_trace(go.Scatter(
                x=sub["sugars_100g"], y=sub["proteins_100g"],
                mode="markers",
                marker=dict(
                    color=sub["blue_ocean"].map({True:"#e8ff47", False:"#3a3a3a"}),
                    size=4, opacity=0.55, line=dict(width=0),
                ),
                showlegend=False,
                hovertemplate="Sugar: %{x:.1f}g | Protein: %{y:.1f}g<extra>" + cat + "</extra>",
            ), row=r+1, col=c+1)
            fig3.add_shape(
                type="rect", x0=0, x1=SUGAR_THRESHOLD, y0=PROTEIN_THRESHOLD, y1=100,
                fillcolor="rgba(232,255,71,0.06)",
                line=dict(color="rgba(232,255,71,0.25)", width=0.8),
                row=r+1, col=c+1,
            )

        fig3.update_layout(**PLOT_THEME, height=n_rows*200, margin=dict(l=40,r=10,t=40,b=40))
        fig3.update_xaxes(gridcolor="#2a2a2a", range=[0, 85])
        fig3.update_yaxes(gridcolor="#2a2a2a", range=[0, 100])
        st.plotly_chart(fig3, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — NutriScore Analysis  (Candidate's Choice)
# ════════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("#### NutriScore Grade Distribution by Category")
    st.markdown(
        '<p style="font-size:12px;color:#888;margin-bottom:4px;">'
        "<b>Candidate's Choice.</b> NutriScore (A–E) is the EU's front-of-pack health label. "
        "Categories dominated by D/E grades present the biggest reformulation opportunity."
        "</p>",
        unsafe_allow_html=True,
    )

    scored = fdf[fdf["nutriscore_grade"].isin(SCORE_MAP.keys())].copy()
    scored["ns_num"] = scored["nutriscore_grade"].map(SCORE_MAP)

    grade_dist = (
        pd.crosstab(scored["primary_category"], scored["nutriscore_grade"], normalize="index") * 100
    )
    grade_dist = grade_dist.reindex(columns=[g for g in GRADE_ORDER if g in grade_dist.columns])

    ns_by_cat = (
        scored.groupby("primary_category")["ns_num"]
        .mean().round(2)
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"ns_num":"avg_score"})
    )

    col1, col2 = st.columns([3, 2])

    with col1:
        fig4 = go.Figure()
        for grade in GRADE_ORDER:
            if grade not in grade_dist.columns:
                continue
            fig4.add_trace(go.Bar(
                y=grade_dist.index, x=grade_dist[grade],
                name=f"Grade {grade.upper()}",
                orientation="h",
                marker_color=NS_COLORS[grade],
                hovertemplate=f"Grade {grade.upper()}: %{{x:.1f}}%<extra>%{{y}}</extra>",
            ))
        fig4.update_layout(
            **PLOT_THEME, barmode="stack", height=380,
            xaxis=dict(title="% of products", ticksuffix="%", gridcolor="#2a2a2a"),
            yaxis=dict(gridcolor="#2a2a2a"),
            legend=dict(bgcolor="#141414", bordercolor="#2a2a2a", borderwidth=1, font=dict(size=11)),
            margin=dict(l=10, r=10, t=10, b=40),
        )
        st.plotly_chart(fig4, use_container_width=True)

    with col2:
        st.markdown("##### Avg NutriScore (1=A · 5=E)")
        fig5 = go.Figure(go.Bar(
            x=ns_by_cat["avg_score"], y=ns_by_cat["primary_category"],
            orientation="h",
            marker=dict(
                color=ns_by_cat["avg_score"],
                colorscale=[[0,"#2d9e2d"],[0.5,"#fecb02"],[1,"#cc1900"]],
                cmin=1, cmax=5,
            ),
            hovertemplate="<b>%{y}</b><br>Avg NutriScore: %{x:.2f}<extra></extra>",
        ))
        fig5.update_layout(
            **PLOT_THEME, height=380,
            xaxis=dict(title="Avg score (1=A, 5=E)", gridcolor="#2a2a2a", range=[1,5]),
            yaxis=dict(gridcolor="#2a2a2a"),
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=40),
        )
        st.plotly_chart(fig5, use_container_width=True)

    worst_cat = ns_by_cat.iloc[0]["primary_category"]
    st.markdown(f"""
    <div class="insight-box">
        <h4>⬡ Candidate's Choice Insight</h4>
        <p>
        <strong>{worst_cat}</strong> has the worst average NutriScore across all categories.
        Launching a NutriScore A or B product here gives an immediate on-shelf competitive advantage —
        especially in EU markets where NutriScore labelling directly influences purchasing decisions.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 4 — Protein Sources  (Bonus Story 5)
# ════════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("#### Top Protein-Source Ingredients in Blue Ocean Products")
    st.markdown(
        '<p style="font-size:12px;color:#888;margin-bottom:16px;">'
        "Keyword frequency across <code>ingredients_text</code> for all High-Protein / Low-Sugar products."
        "</p>",
        unsafe_allow_html=True,
    )

    hp_df    = fdf[fdf["blue_ocean"] & fdf["ingredients_text"].notna()].copy()
    ing_low  = hp_df["ingredients_text"].str.lower()
    counts   = {kw: int(ing_low.str.contains(kw, na=False).sum()) for kw in PROTEIN_KEYWORDS}
    ps       = pd.Series(counts).sort_values(ascending=False)
    ps       = ps[ps > 0].head(12)
    top3     = ps.head(3).index.tolist()

    col_p1, col_p2 = st.columns([3, 2])

    with col_p1:
        bar_colors = ["#e8ff47" if i < 3 else "#3a4a3a" for i in range(len(ps))]
        fig6 = go.Figure(go.Bar(
            y=ps.index, x=ps.values,
            orientation="h",
            marker=dict(color=bar_colors),
            hovertemplate="<b>%{y}</b><br>%{x:,} products<extra></extra>",
        ))
        fig6.update_layout(
            **PLOT_THEME, height=400,
            xaxis=dict(title="Blue Ocean products containing ingredient", gridcolor="#2a2a2a"),
            yaxis=dict(gridcolor="#2a2a2a"),
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=40),
        )
        st.plotly_chart(fig6, use_container_width=True)

    with col_p2:
        st.markdown("##### Top 3 Protein Sources")
        for i, src in enumerate(top3, 1):
            st.markdown(f"""
            <div style="background:#1a1a1a;border:1px solid #2a2a2a;border-left:3px solid #e8ff47;
                        border-radius:4px;padding:12px 16px;margin-bottom:8px;">
                <div style="font-size:10px;color:#888;text-transform:uppercase;letter-spacing:.1em;">#{i}</div>
                <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:700;
                            color:#e8ff47;text-transform:capitalize;">{src}</div>
                <div style="font-size:12px;color:#888;margin-top:2px;">{int(ps[src]):,} products</div>
            </div>
            """, unsafe_allow_html=True)

        if len(top3) >= 2:
            st.markdown(f"""
            <div class="insight-box" style="margin-top:16px;">
                <h4>⬡ R&D Recommendation</h4>
                <p>
                Formulate the new product around <strong>{top3[0].title()}</strong> and
                <strong>{top3[1].title()}</strong> as primary protein carriers — they dominate
                Blue Ocean products and carry strong consumer appeal with proven manufacturing
                scalability.
                </p>
            </div>
            """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="font-size:11px;color:#444;text-align:center;">'
    "Sugar Trap · Market Gap Analysis · Helix CPG Partners · "
    "Data: Open Food Facts (openfoodfacts.org) · CC BY-SA 4.0"
    "</p>",
    unsafe_allow_html=True,
)
