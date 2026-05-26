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
AKG_PATH = BASE_DIR / "data" / "akg (2).csv"
STYLE_PATH = BASE_DIR / "styles/style.css"

# LOAD AKG
@st.cache_data
def load_akg_data(csv_path: Path) -> pd.DataFrame:
    return pd.read_csv(csv_path)

# =========================
# LOAD CSS
# =========================
def load_css(css_path: Path) -> None:
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True
        )


def load_extra_css() -> None:
    st.markdown(
        """
        <style>
        /* =========================
           EXTRA DASHBOARD COMPONENTS
        ========================= */

        .profile-card {
            background: linear-gradient(135deg, #FFFFFF 0%, #EAFBF0 100%);
            border: 1px solid var(--green-border);
            border-radius: 24px;
            padding: 22px;
            margin: 16px 0 24px 0;
            box-shadow: 0 10px 26px rgba(31, 122, 75, 0.08);
        }

        .profile-title {
            font-size: 1.35rem;
            font-weight: 900;
            color: var(--green-dark);
            margin-bottom: 8px;
        }

        .profile-text {
            color: var(--green-muted);
            line-height: 1.55;
        }
        """,
        unsafe_allow_html=True
    )


load_css(STYLE_PATH)
load_extra_css()


# SESSION STATE
def initialize_session_state(akg_df: pd.DataFrame) -> None:
    default_values = {
        "user_name": "",
        "gender": "Female",
        "age": 21,
        "special_condition": "None",
        "condition_month": 0,
        "meal_log": []
    }

    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "akg_calories" not in st.session_state:
        default_akg = calculate_user_akg(
            akg_df=akg_df,
            gender=st.session_state.gender,
            age=st.session_state.age,
            special_condition=st.session_state.special_condition,
            condition_month=st.session_state.condition_month
        )

        st.session_state.akg_calories = default_akg["calories"]
        st.session_state.akg_protein = default_akg["protein"]
        st.session_state.akg_fat = default_akg["fat"]
        st.session_state.akg_carbs = default_akg["carbs"]


# =========================
# DATA FUNCTIONS
# =========================
@st.cache_data
def load_data(csv_path: Path) -> pd.DataFrame:
    return pd.read_csv(csv_path)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Make the app tolerant to slightly different column names.
    """

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
    df = df.rename(
        columns={col: column_map.get(col, col) for col in df.columns}
    )

    return df


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    df = standardize_columns(df)

    required_columns = [
        "name",
        "calories",
        "protein",
        "fat",
        "carbs",
        "image_path"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        st.error(f"Missing required columns: {missing_columns}")
        st.stop()

    for col in ["calories", "protein", "fat", "carbs"]:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df["name"] = df["name"].astype(str).str.strip()

    df = df.dropna(
        subset=["name", "calories", "protein", "fat", "carbs"]
    )

    df = df[df["name"] != ""].copy()

    df = df[
        (df["calories"] > 0) &
        (df["protein"] >= 0) &
        (df["fat"] >= 0) &
        (df["carbs"] >= 0)
    ].copy()

    return df


def calculate_user_akg(
    akg_df: pd.DataFrame,
    gender: str,
    age: int,
    special_condition: str,
    condition_month: int
) -> dict:
    age = float(age)

    # Untuk umur di bawah 10 tahun, AKG tidak dibedakan male/female
    if age < 10:
        base_category = "infants_children"
    else:
        base_category = gender.lower().strip()

    base_row = akg_df[
        (akg_df["age_category"] == base_category) &
        (akg_df["min_age"] <= age) &
        (akg_df["max_age"] >= age)
    ]

    if base_row.empty:
        st.error(
            f"AKG data was not found for age {age} and category {base_category}."
        )
        st.stop()

    base_row = base_row.iloc[0]

    calories = float(base_row["calories"])
    protein = float(base_row["protein"])
    fat = float(base_row["fat"])
    carbs = float(base_row["carbs"])

    if gender == "Female" and special_condition == "Pregnant":
        extra_row = akg_df[
            (akg_df["age_category"] == "pregnant") &
            (akg_df["preg_month_min"] <= condition_month) &
            (akg_df["preg_month_max"] >= condition_month)
        ]

        if not extra_row.empty:
            extra_row = extra_row.iloc[0]
            calories += float(extra_row["calories"])
            protein += float(extra_row["protein"])
            fat += float(extra_row["fat"])
            carbs += float(extra_row["carbs"])

    elif gender == "Female" and special_condition == "Breastfeeding":
        extra_row = akg_df[
            (akg_df["age_category"] == "breastfeeding") &
            (akg_df["bf_month_min"] <= condition_month) &
            (akg_df["bf_month_max"] >= condition_month)
        ]

        if not extra_row.empty:
            extra_row = extra_row.iloc[0]
            calories += float(extra_row["calories"])
            protein += float(extra_row["protein"])
            fat += float(extra_row["fat"])
            carbs += float(extra_row["carbs"])

    return {
        "calories": int(round(calories)),
        "protein": int(round(protein)),
        "fat": round(fat, 1),
        "carbs": int(round(carbs))
    }


def add_nutrition_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    akg_calories = st.session_state.get("akg_calories", 2250)
    akg_protein = st.session_state.get("akg_protein", 60)
    akg_fat = st.session_state.get("akg_fat", 65)
    akg_carbs = st.session_state.get("akg_carbs", 360)

    df["portion_calories"] = akg_calories / df["calories"]

    df["portion_protein"] = np.where(
        df["protein"] > 0,
        akg_protein / df["protein"],
        np.nan
    )

    df.replace(
        [np.inf, -np.inf],
        np.nan,
        inplace=True
    )

    df["portion_calories"] = df["portion_calories"].fillna(1000)
    df["portion_protein"] = df["portion_protein"].fillna(1000)

    df["overall_portions_combined"] = (
        df[["portion_calories", "portion_protein"]]
        .max(axis=1) * 100
    )

    df["efficiency_rank"] = (
        df["overall_portions_combined"]
        .rank(method="dense", ascending=True)
        .astype(int)
    )

    df["calories_akg_pct"] = (
        df["calories"] / akg_calories
    ) * 100

    df["protein_akg_pct"] = (
        df["protein"] / akg_protein
    ) * 100

    df["fat_akg_pct"] = (
        df["fat"] / akg_fat
    ) * 100

    df["carbs_akg_pct"] = (
        df["carbs"] / akg_carbs
    ) * 100

    df["protein_density"] = (
        df["protein"] / df["calories"]
    ) * 100

    df["carbs_to_protein_ratio"] = np.where(
        df["protein"] > 0,
        df["carbs"] / df["protein"],
        np.nan
    )

    return df


def calculate_food_nutrition(
    row: pd.Series,
    portion_gram: float
) -> tuple:
    """
    Convert nutrition per 100 grams into selected portion size.
    """

    calories = row["calories"] * portion_gram / 100
    protein = row["protein"] * portion_gram / 100
    fat = row["fat"] * portion_gram / 100
    carbs = row["carbs"] * portion_gram / 100

    return calories, protein, fat, carbs


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
        coloraxis_colorbar=dict(
            title_font=dict(color="#143D2A"),
            tickfont=dict(color="#143D2A")
        ),
        margin=dict(l=20, r=20, t=60, b=20),
    )

    fig.update_xaxes(
        gridcolor="rgba(63,175,108,0.16)",
        zerolinecolor="rgba(63,175,108,0.22)"
    )

    fig.update_yaxes(
        gridcolor="rgba(63,175,108,0.16)",
        zerolinecolor="rgba(63,175,108,0.22)"
    )

    return fig

# NOTE: AKG + session state must be initialized *before* any UI reads st.session_state.
if not AKG_PATH.exists():
    st.error("AKG file was not found. Put `akg.csv` inside the `data` folder.")
    st.stop()

akg_df = load_akg_data(AKG_PATH)

initialize_session_state(akg_df)

# =========================
# LOAD DATA
# =========================
if not DATA_PATH.exists():
    st.error(
        "CSV file was not found. Put `Foodimages (4).csv` inside the `data` folder."
    )
    st.stop()

raw_df = prepare_data(
    load_data(DATA_PATH)
)

if "working_df" not in st.session_state:
    st.session_state.working_df = raw_df.copy()


# =========================
# SIDEBAR USER PROFILE
# =========================
st.sidebar.markdown("## User Profile")
st.sidebar.caption(
    "Input your profile to estimate daily nutrition needs."
)

with st.sidebar.form("profile_form"):

    input_name = st.text_input(
        "Name",
        value=st.session_state.user_name
    )

    gender_options = ["Female", "Male"]

    input_gender = st.selectbox(
        "Gender",
        gender_options,
        index=gender_options.index(st.session_state.gender)
        if st.session_state.gender in gender_options
        else 0
    )

    input_age = st.number_input(
        "Age",
        min_value=0,
        max_value=100,
        value=int(st.session_state.age),
        step=1
    )

    if input_gender == "Female":
        condition_options = [
            "None",
            "Pregnant",
            "Breastfeeding"
        ]
    else:
        condition_options = ["None"]

    saved_condition = st.session_state.special_condition

    if saved_condition not in condition_options:
        saved_condition = "None"

    input_special_condition = st.selectbox(
        "Special Condition",
        condition_options,
        index=condition_options.index(saved_condition)
    )

    if input_special_condition != "None":
        input_condition_month = st.number_input(
            "Condition Month",
            min_value=1,
            max_value=24,
            value=max(1, int(st.session_state.condition_month)),
            step=1
        )
    else:
        input_condition_month = 0

    apply_profile = st.form_submit_button(
        "Apply Profile"
    )


if apply_profile:
    estimated_akg = calculate_user_akg(
        akg_df=akg_df,
        gender=input_gender,
        age=int(input_age),
        special_condition=input_special_condition,
        condition_month=int(input_condition_month)
    )

    st.session_state.user_name = input_name
    st.session_state.gender = input_gender
    st.session_state.age = int(input_age)
    st.session_state.special_condition = input_special_condition
    st.session_state.condition_month = int(input_condition_month)

    st.session_state.akg_calories = estimated_akg["calories"]
    st.session_state.akg_protein = estimated_akg["protein"]
    st.session_state.akg_fat = estimated_akg["fat"]
    st.session_state.akg_carbs = estimated_akg["carbs"]

    st.rerun()


# =========================
# SIDEBAR DAILY NEEDS
# =========================
st.sidebar.markdown("## Daily Nutrition Needs")
st.sidebar.caption(
    "Estimated from your profile. You can still edit the values manually."
)

st.sidebar.number_input(
    "Calories Need (kcal)",
    min_value=1,
    max_value=6000,
    step=50,
    key="akg_calories"
)

st.sidebar.number_input(
    "Protein Need (g)",
    min_value=1,
    max_value=400,
    step=5,
    key="akg_protein"
)

st.sidebar.number_input(
    "Fat Need (g)",
    min_value=1,
    max_value=300,
    step=5,
    key="akg_fat"
)

st.sidebar.number_input(
    "Carbohydrate Need (g)",
    min_value=1,
    max_value=900,
    step=10,
    key="akg_carbs"
)


# =========================
# SIDEBAR FILTERS
# =========================
working_df = add_nutrition_metrics(
    st.session_state.working_df
)

st.sidebar.markdown("### Filters")

search_food = st.sidebar.text_input(
    "Search food"
)

calorie_range = st.sidebar.slider(
    "Calories Range",
    float(working_df["calories"].min()),
    float(working_df["calories"].max()),
    (
        float(working_df["calories"].min()),
        float(working_df["calories"].max())
    )
)

protein_range = st.sidebar.slider(
    "Protein Range",
    float(working_df["protein"].min()),
    float(working_df["protein"].max()),
    (
        float(working_df["protein"].min()),
        float(working_df["protein"].max())
    )
)

top_n = st.sidebar.slider(
    "Number of Ranked Foods",
    5,
    30,
    10
)


# =========================
# FILTER DATA
# =========================
filtered_df = working_df[
    (working_df["calories"] >= calorie_range[0]) &
    (working_df["calories"] <= calorie_range[1]) &
    (working_df["protein"] >= protein_range[0]) &
    (working_df["protein"] <= protein_range[1])
].copy()

if search_food:
    filtered_df = filtered_df[
        filtered_df["name"].str.contains(
            search_food,
            case=False,
            na=False
        )
    ]

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
            Analyze food images and nutrition data using calories, protein, fat,
            carbohydrates, portion efficiency, user-based AKG estimation,
            daily food tracking, and automatic insight summaries.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================
# USER PROFILE SUMMARY
# =========================
condition_text = st.session_state.special_condition

if condition_text != "None":
    condition_text = (
        f"{condition_text}, month {st.session_state.condition_month}"
    )

st.markdown(
    f"""
    <div class="profile-card">
        <div class="profile-title">
            Personal Nutrition Profile
        </div>
        <div class="profile-text">
            <b>Name:</b> {st.session_state.user_name if st.session_state.user_name else "Not filled yet"}<br>
            <b>Gender:</b> {st.session_state.gender}<br>
            <b>Age:</b> {st.session_state.age} years old<br>
            <b>Special condition:</b> {condition_text}<br><br>
            Estimated daily needs:
            <b>{st.session_state.akg_calories} kcal</b>,
            <b>{st.session_state.akg_protein} g protein</b>,
            <b>{st.session_state.akg_fat} g fat</b>, and
            <b>{st.session_state.akg_carbs} g carbohydrates</b>.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================
# KPI
# =========================
best_row = filtered_df.sort_values(
    "overall_portions_combined"
).iloc[0]

highest_protein_row = filtered_df.sort_values(
    "protein",
    ascending=False
).iloc[0]

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Foods",
    f"{len(filtered_df):,}"
)

col2.metric(
    "Average Calories",
    f"{filtered_df['calories'].mean():.2f} kcal"
)

col3.metric(
    "Average Protein",
    f"{filtered_df['protein'].mean():.2f} g"
)

col4.metric(
    "Most Efficient Food",
    best_row["name"]
)


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
            It requires approximately <b>{best_row['overall_portions_combined']:.1f} g</b>
            to satisfy the combined calorie and protein target logic used in this dashboard.
        </div>
    </div>

    <div class="insight-card">
        <div class="insight-title">Protein concentration</div>
        <div class="insight-text">
            <b>{highest_protein_row['name']}</b> has the highest protein value in the current view,
            with <b>{highest_protein_row['protein']:.1f} g protein per 100 g</b>.
            This makes it useful for comparing high-protein foods against their calorie level.
        </div>
    </div>

    <div class="insight-card">
        <div class="insight-title">Overall nutrition pattern</div>
        <div class="insight-text">
            The filtered dataset has an average of <b>{avg_cal:.1f} kcal</b>
            and <b>{avg_protein:.1f} g protein</b> per 100 g.
            The median efficiency requirement is <b>{median_eff:.1f} g</b>,
            so foods below this value are relatively more efficient than the typical item
            in the selected range.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================
# EFFICIENCY RANKING
# =========================
st.markdown("## Most Efficient Foods")

top_efficient = filtered_df.sort_values(
    "overall_portions_combined"
).head(top_n)

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

fig_eff.update_layout(
    yaxis=dict(autorange="reversed"),
    xaxis_title="Required grams",
    yaxis_title="Food name"
)

fig_eff.update_traces(
    texttemplate="%{text:.1f} g",
    textposition="outside"
)

st.plotly_chart(
    apply_plot_theme(fig_eff),
    use_container_width=True
)

st.info(
    "Lower required grams means the food is more efficient for meeting the combined calorie and protein target logic."
)


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
    hover_data=[
        "calories",
        "protein",
        "fat",
        "carbs",
        "overall_portions_combined"
    ],
    title="Calories and Protein Distribution"
)

st.plotly_chart(
    apply_plot_theme(fig_scatter),
    use_container_width=True
)


# =========================
# PERSONAL NUTRITION CHECKER
# =========================
st.markdown("## Check Food Nutrition by Portion")

st.markdown(
    """
    Use this section to check how much nutrition you will get from a specific food
    based on the portion size you enter.
    """
)

checker_col1, checker_col2 = st.columns([2, 1])

with checker_col1:
    check_food = st.selectbox(
        "Choose a food to check",
        filtered_df["name"].sort_values().unique(),
        key="check_food"
    )

with checker_col2:
    check_portion = st.number_input(
        "Portion size (grams)",
        min_value=1,
        max_value=3000,
        value=100,
        step=10,
        key="check_portion"
    )

check_row = filtered_df[
    filtered_df["name"] == check_food
].iloc[0]

check_calories, check_protein, check_fat, check_carbs = calculate_food_nutrition(
    check_row,
    check_portion
)

st.markdown(
    f"### Nutrition content for {check_portion} g of {check_food}"
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Calories",
    f"{check_calories:.2f} kcal",
    f"{(check_calories / st.session_state.akg_calories) * 100:.1f}% of daily need"
)

col2.metric(
    "Protein",
    f"{check_protein:.2f} g",
    f"{(check_protein / st.session_state.akg_protein) * 100:.1f}% of daily need"
)

col3.metric(
    "Fat",
    f"{check_fat:.2f} g",
    f"{(check_fat / st.session_state.akg_fat) * 100:.1f}% of daily need"
)

col4.metric(
    "Carbohydrates",
    f"{check_carbs:.2f} g",
    f"{(check_carbs / st.session_state.akg_carbs) * 100:.1f}% of daily need"
)


# =========================
# ADDED FOOD TODAY
# =========================
st.markdown("## Added Food Today")

st.markdown(
    """
    Add foods you eat today. The dashboard will calculate total calories,
    protein, fat, and carbohydrates, then compare them with your daily needs.
    """
)

add_col1, add_col2, add_col3 = st.columns([2, 1, 1])

with add_col1:
    add_food = st.selectbox(
        "Choose food to add",
        filtered_df["name"].sort_values().unique(),
        key="add_food"
    )

with add_col2:
    add_portion = st.number_input(
        "Add portion (grams)",
        min_value=1,
        max_value=3000,
        value=100,
        step=10,
        key="add_portion"
    )

add_row = filtered_df[
    filtered_df["name"] == add_food
].iloc[0]

add_calories, add_protein, add_fat, add_carbs = calculate_food_nutrition(
    add_row,
    add_portion
)

with add_col3:
    st.write("")
    st.write("")

    if st.button("Add Food Today"):
        st.session_state.meal_log.append(
            {
                "Food": add_food,
                "Portion (g)": add_portion,
                "Calories": round(add_calories, 2),
                "Protein": round(add_protein, 2),
                "Fat": round(add_fat, 2),
                "Carbohydrates": round(add_carbs, 2)
            }
        )


# =========================
# MEAL LOG CALCULATION
# =========================
meal_df = pd.DataFrame(
    st.session_state.meal_log
)

if meal_df.empty:
    total_calories = 0
    total_protein = 0
    total_fat = 0
    total_carbs = 0

else:
    total_calories = meal_df["Calories"].sum()
    total_protein = meal_df["Protein"].sum()
    total_fat = meal_df["Fat"].sum()
    total_carbs = meal_df["Carbohydrates"].sum()

# =========================
# DAILY NUTRITION SUMMARY
# =========================
st.markdown("## Daily Nutrition Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Calories Today",
    f"{total_calories:.2f} kcal",
    f"{(total_calories / st.session_state.akg_calories) * 100:.1f}%"
)

col2.metric(
    "Protein Today",
    f"{total_protein:.2f} g",
    f"{(total_protein / st.session_state.akg_protein) * 100:.1f}%"
)

col3.metric(
    "Fat Today",
    f"{total_fat:.2f} g",
    f"{(total_fat / st.session_state.akg_fat) * 100:.1f}%"
)

col4.metric(
    "Carbohydrates Today",
    f"{total_carbs:.2f} g",
    f"{(total_carbs / st.session_state.akg_carbs) * 100:.1f}%"
)


# =========================
# DAILY TARGET PROGRESS
# =========================
st.markdown("## Daily Target Progress")

progress_items = [
    (
        "Calories",
        total_calories,
        st.session_state.akg_calories
    ),
    (
        "Protein",
        total_protein,
        st.session_state.akg_protein
    ),
    (
        "Fat",
        total_fat,
        st.session_state.akg_fat
    ),
    (
        "Carbohydrates",
        total_carbs,
        st.session_state.akg_carbs
    )
]

for label, consumed, target in progress_items:
    progress_value = consumed / target
    progress_percentage = progress_value * 100

    st.write(
        f"{label}: {consumed:.2f} / {target:.2f} "
        f"({progress_percentage:.1f}% of daily need)"
    )

    st.progress(
        min(float(progress_value), 1.0)
    )


# =========================
# FOOD LOG TABLE
# =========================
st.markdown("## Food Log Table")

meal_df = pd.DataFrame(
    st.session_state.meal_log
)

if meal_df.empty:
    st.info("No food has been added today.")

else:
    table_col, action_col = st.columns([4, 1])

    with table_col:
        st.dataframe(
            meal_df,
            use_container_width=True
        )

        csv_data = meal_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="Download Food Log CSV",
            data=csv_data,
            file_name="food_log_today.csv",
            mime="text/csv"
        )

    with action_col:
        st.markdown("### Actions")

        food_options = meal_df["Food"].unique().tolist()

        selected_delete_food = st.selectbox(
            "Select food",
            food_options,
            key="selected_delete_food"
        )

        if st.button("Delete Food", use_container_width=True):
            st.session_state.meal_log = [
                food for food in st.session_state.meal_log
                if food["Food"] != selected_delete_food
            ]

            st.rerun()

        if st.button("Clear All", use_container_width=True):
            st.session_state.meal_log = []

            st.rerun()


# =========================
# TOP PROTEIN
# =========================
st.markdown("## Highest Protein Foods")

top_protein = filtered_df.sort_values(
    "protein",
    ascending=False
).head(top_n)

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

fig_protein.update_layout(
    yaxis=dict(autorange="reversed"),
    xaxis_title="Protein per 100 g",
    yaxis_title="Food name"
)

fig_protein.update_traces(
    texttemplate="%{text:.1f} g",
    textposition="outside"
)

st.plotly_chart(
    apply_plot_theme(fig_protein),
    use_container_width=True
)


# =========================
# NUTRIENT DISTRIBUTION
# =========================
st.markdown("## Nutrient Distributions")

col1, col2 = st.columns(2)

with col1:
    fig_cal = px.histogram(
        filtered_df,
        x="calories",
        nbins=30,
        color_discrete_sequence=["#7BD89B"],
        title="Calories Distribution"
    )

    st.plotly_chart(
        apply_plot_theme(fig_cal),
        use_container_width=True
    )

with col2:
    fig_protein_hist = px.histogram(
        filtered_df,
        x="protein",
        nbins=30,
        color_discrete_sequence=["#3FAF6C"],
        title="Protein Distribution"
    )

    st.plotly_chart(
        apply_plot_theme(fig_protein_hist),
        use_container_width=True
    )

col3, col4 = st.columns(2)

with col3:
    fig_fat = px.histogram(
        filtered_df,
        x="fat",
        nbins=30,
        color_discrete_sequence=["#9DE3B1"],
        title="Fat Distribution"
    )

    st.plotly_chart(
        apply_plot_theme(fig_fat),
        use_container_width=True
    )

with col4:
    fig_carbs = px.histogram(
        filtered_df,
        x="carbs",
        nbins=30,
        color_discrete_sequence=["#BCEBCB"],
        title="Carbohydrates Distribution"
    )

    st.plotly_chart(
        apply_plot_theme(fig_carbs),
        use_container_width=True
    )


# =========================
# IMAGE PREVIEW
# =========================
st.markdown("## Dataset Image Preview")

preview_food = st.selectbox(
    "Select a dataset image",
    filtered_df["name"].sort_values().unique(),
    key="preview_food"
)

preview_row = filtered_df[
    filtered_df["name"] == preview_food
].iloc[0]

image_path = resolve_image_path(
    preview_row["image_path"]
)

if image_path.exists():
    st.image(
        str(image_path),
        caption=preview_food,
        width=380
    )

else:
    st.warning(
        f"Image was not found at this path: {image_path}"
    )



