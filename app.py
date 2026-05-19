import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Food Nutrition Dashboard",
    layout="wide"
)


# =========================
# PATH CONFIG
# =========================
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "Foodimages (4).csv"
STYLE_PATH = BASE_DIR / "styles/style.css"


# =========================
# LOAD CSS
# =========================
def load_css(css_path: Path) -> None:
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


load_css(STYLE_PATH)


# =========================
# DATA FUNCTIONS
# =========================
@st.cache_data
def load_data(csv_path: Path) -> pd.DataFrame:
    return pd.read_csv(csv_path)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Make the app tolerant to slightly different column names."""
    column_map = {
        "foodname": "name",
        "food_name": "name",
        "foodname_100g": "name",
        "nama_makanan": "name",
        "total_fat": "fat",
        "lemak": "fat",
        "carbohydrates": "carbs",
        "carbohydrate": "carbs",
        "karbohidrat": "carbs",
        "image": "image_path",
        "img_path": "image_path",
        "path": "image_path",
    }

    df = df.copy()
    df.columns = [col.strip() for col in df.columns]
    df = df.rename(columns={col: column_map.get(col, col) for col in df.columns})
    return df


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    df = standardize_columns(df)

    required_columns = ["name", "calories", "protein", "fat", "carbs", "image_path"]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        st.error(f"Missing required columns: {missing_columns}")
        st.stop()

    for col in ["calories", "protein", "fat", "carbs"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["name"] = df["name"].astype(str).str.strip()
    df = df.dropna(subset=["name", "calories", "protein", "fat", "carbs"])
    df = df[df["name"] != ""].copy()

    df = df[(df["calories"] > 0) & (df["protein"] >= 0) & (df["fat"] >= 0) & (df["carbs"] >= 0)].copy()

    return df


def add_nutrition_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    akg_calories = st.session_state.get("akg_calories", 2250)
    akg_protein = st.session_state.get("akg_protein", 60)
    akg_fat = st.session_state.get("akg_fat", 67)
    akg_carbs = st.session_state.get("akg_carbs", 325)

    df["portion_calories"] = akg_calories / df["calories"]
    df["portion_protein"] = np.where(df["protein"] > 0, akg_protein / df["protein"], np.nan)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    df["portion_calories"] = df["portion_calories"].fillna(1000)
    df["portion_protein"] = df["portion_protein"].fillna(1000)

    df["overall_portions_combined"] = df[["portion_calories", "portion_protein"]].max(axis=1) * 100
    df["efficiency_rank"] = df["overall_portions_combined"].rank(method="dense", ascending=True).astype(int)

    df["calories_akg_pct"] = (df["calories"] / akg_calories) * 100
    df["protein_akg_pct"] = (df["protein"] / akg_protein) * 100
    df["fat_akg_pct"] = (df["fat"] / akg_fat) * 100
    df["carbs_akg_pct"] = (df["carbs"] / akg_carbs) * 100

    df["protein_density"] = (df["protein"] / df["calories"]) * 100
    df["carbs_to_protein_ratio"] = np.where(df["protein"] > 0, df["carbs"] / df["protein"], np.nan)

    return df


def resolve_image_path(path_value: str) -> Path:
    path = Path(str(path_value))
    if path.is_absolute():
        return path
    return BASE_DIR / path


def apply_plot_theme(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#143D2A"),
        title_font=dict(color="#143D2A", size=20),
        coloraxis_colorbar=dict(title_font=dict(color="#143D2A"), tickfont=dict(color="#143D2A")),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    fig.update_xaxes(gridcolor="rgba(63,175,108,0.16)", zerolinecolor="rgba(63,175,108,0.22)")
    fig.update_yaxes(gridcolor="rgba(63,175,108,0.16)", zerolinecolor="rgba(63,175,108,0.22)")
    return fig


# =========================
# LOAD DATA
# =========================
if not DATA_PATH.exists():
    st.error("CSV file was not found. Put `Foodimages (4).csv` inside the `data` folder.")
    st.stop()

raw_df = prepare_data(load_data(DATA_PATH))

if "working_df" not in st.session_state:
    st.session_state.working_df = raw_df.copy()


# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("## Dashboard Controls")
st.sidebar.caption("Filter, delete food rows, and adjust nutrition targets.")

with st.sidebar.expander("Nutrition Targets", expanded=False):
    st.session_state.akg_calories = st.number_input("Daily Calories Target (kcal)", min_value=1, value=2250, step=50)
    st.session_state.akg_protein = st.number_input("Daily Protein Target (g)", min_value=1, value=60, step=5)
    st.session_state.akg_fat = st.number_input("Daily Fat Target (g)", min_value=1, value=67, step=5)
    st.session_state.akg_carbs = st.number_input("Daily Carbohydrate Target (g)", min_value=1, value=325, step=10)

working_df = add_nutrition_metrics(st.session_state.working_df)

st.sidebar.markdown("### Delete Food")
delete_name = st.sidebar.text_input("Enter food name to delete")
delete_mode = st.sidebar.radio("Delete mode", ["Exact match", "Contains text"], horizontal=False)

if st.sidebar.button("Delete from Dashboard"):
    if delete_name.strip() == "":
        st.sidebar.warning("Please enter a food name first.")
    else:
        before_count = len(st.session_state.working_df)
        if delete_mode == "Exact match":
            mask_delete = st.session_state.working_df["name"].str.lower() == delete_name.strip().lower()
        else:
            mask_delete = st.session_state.working_df["name"].str.contains(delete_name.strip(), case=False, na=False)

        st.session_state.working_df = st.session_state.working_df[~mask_delete].copy()
        deleted_count = before_count - len(st.session_state.working_df)

        if deleted_count > 0:
            st.sidebar.success(f"Deleted {deleted_count} row(s).")
            st.rerun()
        else:
            st.sidebar.info("No matching food was found.")

if st.sidebar.button("Reset Deleted Data"):
    st.session_state.working_df = raw_df.copy()
    st.rerun()

working_df = add_nutrition_metrics(st.session_state.working_df)

st.sidebar.markdown("### Filters")
search_food = st.sidebar.text_input("Search food")

calorie_range = st.sidebar.slider(
    "Calories Range",
    float(working_df["calories"].min()),
    float(working_df["calories"].max()),
    (float(working_df["calories"].min()), float(working_df["calories"].max()))
)

protein_range = st.sidebar.slider(
    "Protein Range",
    float(working_df["protein"].min()),
    float(working_df["protein"].max()),
    (float(working_df["protein"].min()), float(working_df["protein"].max()))
)

top_n = st.sidebar.slider("Number of Ranked Foods", 5, 30, 10)

filtered_df = working_df[
    (working_df["calories"] >= calorie_range[0]) &
    (working_df["calories"] <= calorie_range[1]) &
    (working_df["protein"] >= protein_range[0]) &
    (working_df["protein"] <= protein_range[1])
].copy()

if search_food:
    filtered_df = filtered_df[filtered_df["name"].str.contains(search_food, case=False, na=False)]

if filtered_df.empty:
    st.warning("No data matches the selected filters.")
    st.stop()


# =========================
# HEADER
# =========================
st.markdown(
    """
    <div class="hero-card">
        <div class="hero-title">Food Nutrition Intelligence Dashboard</div>
        <div class="hero-subtitle">
            Analyze food images and nutrition data using calories, protein, fat, carbohydrates,
            portion efficiency, AKG contribution, and automatic insight summaries.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================
# KPI
# =========================
best_row = filtered_df.sort_values("overall_portions_combined").iloc[0]
highest_protein_row = filtered_df.sort_values("protein", ascending=False).iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Foods", f"{len(filtered_df):,}")
col2.metric("Average Calories", f"{filtered_df['calories'].mean():.2f} kcal")
col3.metric("Average Protein", f"{filtered_df['protein'].mean():.2f} g")
col4.metric("Most Efficient Food", best_row["name"])


# =========================
# INSIGHTS
# =========================
st.markdown("## Key Insights")

avg_cal = filtered_df["calories"].mean()
avg_protein = filtered_df["protein"].mean()
median_eff = filtered_df["overall_portions_combined"].median()

st.markdown(
    f"""
    <div class="insight-card">
        <div class="insight-title">Best efficiency candidate</div>
        <div class="insight-text">
            <b>{best_row['name']}</b> is the most efficient food in the current filtered data.
            It requires approximately <b>{best_row['overall_portions_combined']:.1f} g</b> to satisfy both
            the calorie and protein target logic used in this dashboard.
        </div>
    </div>
    <div class="insight-card">
        <div class="insight-title">Protein concentration</div>
        <div class="insight-text">
            <b>{highest_protein_row['name']}</b> has the highest protein value in the current view,
            with <b>{highest_protein_row['protein']:.1f} g protein per 100 g</b>. This makes it useful
            for comparing high-protein foods against their calorie level.
        </div>
    </div>
    <div class="insight-card">
        <div class="insight-title">Overall nutrition pattern</div>
        <div class="insight-text">
            The filtered dataset has an average of <b>{avg_cal:.1f} kcal</b> and
            <b>{avg_protein:.1f} g protein</b> per 100 g. The median efficiency requirement is
            <b>{median_eff:.1f} g</b>, so foods below this value are relatively more efficient
            than the typical item in the selected range.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================
# EFFICIENCY RANKING
# =========================
st.markdown("## Most Efficient Foods")
top_efficient = filtered_df.sort_values("overall_portions_combined").head(top_n)

fig_eff = px.bar(
    top_efficient,
    x="overall_portions_combined",
    y="name",
    orientation="h",
    color="overall_portions_combined",
    color_continuous_scale="Greens_r",
    hover_data=["calories", "protein", "fat", "carbs"],
    text="overall_portions_combined",
    title="Top Foods by Portion Efficiency"
)
fig_eff.update_layout(yaxis=dict(autorange="reversed"), xaxis_title="Required grams", yaxis_title="Food name")
fig_eff.update_traces(texttemplate="%{text:.1f} g", textposition="outside")
st.plotly_chart(apply_plot_theme(fig_eff), use_container_width=True)

st.info("Lower required grams means the food is more efficient for meeting the combined calorie and protein target logic.")


# =========================
# CALORIES VS PROTEIN
# =========================
st.markdown("## Calories vs Protein Relationship")
fig_scatter = px.scatter(
    filtered_df,
    x="calories",
    y="protein",
    size="fat",
    color="overall_portions_combined",
    color_continuous_scale="Greens_r",
    hover_name="name",
    hover_data=["calories", "protein", "fat", "carbs", "overall_portions_combined"],
    title="Calories and Protein Distribution"
)
st.plotly_chart(apply_plot_theme(fig_scatter), use_container_width=True)


# =========================
# AKG PROGRESS BAR
# =========================
st.markdown("## Nutrition Target Progress")
selected_food = st.selectbox("Select a food", filtered_df["name"].sort_values().unique())
selected_row = filtered_df[filtered_df["name"] == selected_food].iloc[0]

portion_gram = st.slider("Food portion size (grams)", 50, 1000, 100)

calories_consumed = selected_row["calories"] * portion_gram / 100
protein_consumed = selected_row["protein"] * portion_gram / 100
fat_consumed = selected_row["fat"] * portion_gram / 100
carbs_consumed = selected_row["carbs"] * portion_gram / 100

st.markdown(f"### Nutrition content for {portion_gram} g of {selected_food}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Calories", f"{calories_consumed:.2f} kcal")
col2.metric("Protein", f"{protein_consumed:.2f} g")
col3.metric("Fat", f"{fat_consumed:.2f} g")
col4.metric("Carbohydrates", f"{carbs_consumed:.2f} g")

progress_items = [
    ("Calories", calories_consumed / st.session_state.akg_calories),
    ("Protein", protein_consumed / st.session_state.akg_protein),
    ("Fat", fat_consumed / st.session_state.akg_fat),
    ("Carbohydrates", carbs_consumed / st.session_state.akg_carbs),
]

for label, value in progress_items:
    st.write(f"{label}: {value * 100:.1f}% of daily target")
    st.progress(min(float(value), 1.0))


# =========================
# TOP PROTEIN
# =========================
st.markdown("## Highest Protein Foods")
top_protein = filtered_df.sort_values("protein", ascending=False).head(top_n)

fig_protein = px.bar(
    top_protein,
    x="protein",
    y="name",
    orientation="h",
    color="protein",
    color_continuous_scale="Greens",
    hover_data=["calories", "fat", "carbs"],
    text="protein",
    title="Top Foods by Protein per 100 g"
)
fig_protein.update_layout(yaxis=dict(autorange="reversed"), xaxis_title="Protein per 100 g", yaxis_title="Food name")
fig_protein.update_traces(texttemplate="%{text:.1f} g", textposition="outside")
st.plotly_chart(apply_plot_theme(fig_protein), use_container_width=True)


# =========================
# NUTRIENT DISTRIBUTION
# =========================
st.markdown("## Nutrient Distributions")
col1, col2 = st.columns(2)

with col1:
    fig_cal = px.histogram(filtered_df, x="calories", nbins=30, color_discrete_sequence=["#7BD89B"], title="Calories Distribution")
    st.plotly_chart(apply_plot_theme(fig_cal), use_container_width=True)

with col2:
    fig_protein_hist = px.histogram(filtered_df, x="protein", nbins=30, color_discrete_sequence=["#3FAF6C"], title="Protein Distribution")
    st.plotly_chart(apply_plot_theme(fig_protein_hist), use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    fig_fat = px.histogram(filtered_df, x="fat", nbins=30, color_discrete_sequence=["#9DE3B1"], title="Fat Distribution")
    st.plotly_chart(apply_plot_theme(fig_fat), use_container_width=True)

with col4:
    fig_carbs = px.histogram(filtered_df, x="carbs", nbins=30, color_discrete_sequence=["#BCEBCB"], title="Carbohydrates Distribution")
    st.plotly_chart(apply_plot_theme(fig_carbs), use_container_width=True)


# =========================
# AI PREDICTION SIMULATION
# =========================
st.markdown("## Food Image Upload and AI Prediction Simulation")
uploaded_file = st.file_uploader("Upload a food image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded image", use_container_width=True)
    st.warning("The real AI model has not been connected yet. This section currently simulates prediction using the most efficient food from the filtered dataset.")

    predicted_row = top_efficient.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Predicted Food", predicted_row["name"])
    col2.metric("Calories / 100 g", f"{predicted_row['calories']:.2f} kcal")
    col3.metric("Protein / 100 g", f"{predicted_row['protein']:.2f} g")
    col4.metric("Efficiency", f"{predicted_row['overall_portions_combined']:.2f} g")


# =========================
# IMAGE PREVIEW
# =========================
st.markdown("## Dataset Image Preview")
preview_food = st.selectbox("Select a dataset image", filtered_df["name"].sort_values().unique(), key="preview_food")
preview_row = filtered_df[filtered_df["name"] == preview_food].iloc[0]
image_path = resolve_image_path(preview_row["image_path"])

if image_path.exists():
    st.image(str(image_path), caption=preview_food, width=380)
else:
    st.warning(f"Image was not found at this path: {image_path}")


# =========================
# DATA TABLE AND DOWNLOAD
# =========================
st.markdown("## Food Data Table")
table_columns = [
    "name", "calories", "protein", "fat", "carbs",
    "overall_portions_combined", "efficiency_rank",
    "calories_akg_pct", "protein_akg_pct", "fat_akg_pct", "carbs_akg_pct"
]

display_table = filtered_df[table_columns].sort_values("overall_portions_combined").reset_index(drop=True)
st.dataframe(display_table, use_container_width=True)

csv_data = st.session_state.working_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download Current Dataset After Deletion",
    data=csv_data,
    file_name="foodimages_updated.csv",
    mime="text/csv"
)
