import os
from pathlib import Path
import html
import textwrap

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image
import streamlit.components.v1 as components
import tensorflow as tf
import keras

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
DATA_PATH = BASE_DIR / "data" / "nutrition_table_cleaned.csv"
AKG_PATH = BASE_DIR / "data" / "akg.csv"
STYLE_PATH = BASE_DIR / "styles/style.css"
ASSETS_DIR = BASE_DIR / "assets"
MODEL_PATH = BASE_DIR / "models" / "best_nutrivision_cnn_food101_akg.keras"

@keras.saving.register_keras_serializable(package="NutriVision")
class NutritionFromClassProbability(keras.layers.Layer):
    def __init__(self, nutrition_table_norm, **kwargs):
        super().__init__(**kwargs)

        nutrition_table_norm = np.array(
            nutrition_table_norm,
            dtype="float32"
        )

        self.nutrition_table_norm = self.add_weight(
            name="nutrition_table_norm",
            shape=nutrition_table_norm.shape,
            initializer=keras.initializers.Constant(nutrition_table_norm),
            trainable=False
        )

    def call(self, class_probs):
        return tf.matmul(class_probs, self.nutrition_table_norm)

    def get_config(self):
        config = super().get_config()
        config.update({
            "nutrition_table_norm": self.nutrition_table_norm.numpy().tolist()
        })
        return config

@keras.saving.register_keras_serializable(package="NutriVision")
class WeightedNutritionMAELoss(keras.losses.Loss):
    def __init__(self, nutrient_weights=None, **kwargs):
        super().__init__(**kwargs)

        if nutrient_weights is None:
            nutrient_weights = [1.0] * 8

        self.nutrient_weights = tf.constant(
            nutrient_weights,
            dtype=tf.float32
        )

    def call(self, y_true, y_pred):
        error = tf.abs(y_true - y_pred)
        weighted_error = error * self.nutrient_weights
        return tf.reduce_mean(weighted_error)

    def get_config(self):
        config = super().get_config()
        config.update({
            "nutrient_weights": self.nutrient_weights.numpy().tolist()
        })
        return config
    
# LOAD AKG
@st.cache_data
def load_akg_data(csv_path: Path) -> pd.DataFrame:
    akg_df = pd.read_csv(csv_path)

    akg_df.columns = [
        col.strip().lower().replace(" ", "_")
        for col in akg_df.columns
    ]

    akg_column_map = {
        "calories_kcal": "calories",
        "protein_g": "protein",
        "fat_g": "fat",
        "carbs_g": "carbs",
        "fiber_g": "fiber",
        "calcium_mg": "calcium",
        "iron_mg": "iron",
        "vitamin_c_mg": "vitamin_c",
    }

    akg_df = akg_df.rename(
        columns={col: akg_column_map.get(col, col) for col in akg_df.columns}
    )

    return akg_df

# =========================
# LOAD CSS
# =========================
def load_css(css_path: Path) -> None:
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True
        )
        
load_css(STYLE_PATH)

def load_food_model(model_path: Path):
    if not model_path.exists():
        st.error(
            "Model file was not found. Put `best_nutrivision_cnn_food101_akg.keras` inside the `models` folder."
        )
        st.stop()

    custom_objects = {
        "NutritionFromClassProbability": NutritionFromClassProbability,
        "NutriVision>NutritionFromClassProbability": NutritionFromClassProbability,
        "WeightedNutritionMAELoss": WeightedNutritionMAELoss,
        "NutriVision>WeightedNutritionMAELoss": WeightedNutritionMAELoss,
    }

    try:
        with keras.saving.custom_object_scope(custom_objects):
            model = keras.models.load_model(
                str(model_path),
                custom_objects=custom_objects,
                compile=False,
                safe_mode=False
            )

        return model

    except Exception as e:
        st.error("Model gagal dimuat. Ini detail error aslinya:")
        st.exception(e)
        st.stop()

FOOD101_CLASSES = [
    "apple_pie", "baby_back_ribs", "baklava", "beef_carpaccio", "beef_tartare",
    "beet_salad", "beignets", "bibimbap", "bread_pudding", "breakfast_burrito",
    "bruschetta", "caesar_salad", "cannoli", "caprese_salad", "carrot_cake",
    "ceviche", "cheesecake", "cheese_plate", "chicken_curry", "chicken_quesadilla",
    "chicken_wings", "chocolate_cake", "chocolate_mousse", "churros", "clam_chowder",
    "club_sandwich", "crab_cakes", "creme_brulee", "croque_madame", "cup_cakes",
    "deviled_eggs", "donuts", "dumplings", "edamame", "eggs_benedict",
    "escargots", "falafel", "filet_mignon", "fish_and_chips", "foie_gras",
    "french_fries", "french_onion_soup", "french_toast", "fried_calamari",
    "fried_rice", "frozen_yogurt", "garlic_bread", "gnocchi", "greek_salad",
    "grilled_cheese_sandwich", "grilled_salmon", "guacamole", "gyoza",
    "hamburger", "hot_and_sour_soup", "hot_dog", "huevos_rancheros",
    "hummus", "ice_cream", "lasagna", "lobster_bisque", "lobster_roll_sandwich",
    "macaroni_and_cheese", "macarons", "miso_soup", "mussels", "nachos",
    "omelette", "onion_rings", "oysters", "pad_thai", "paella",
    "pancakes", "panna_cotta", "peking_duck", "pho", "pizza",
    "pork_chop", "poutine", "prime_rib", "pulled_pork_sandwich", "ramen",
    "ravioli", "red_velvet_cake", "risotto", "samosa", "sashimi",
    "scallops", "seaweed_salad", "shrimp_and_grits", "spaghetti_bolognese",
    "spaghetti_carbonara", "spring_rolls", "steak", "strawberry_shortcake",
    "sushi", "tacos", "takoyaki", "tiramisu", "tuna_tartare",
    "waffles"
]

def preprocess_uploaded_image(uploaded_file):
    image = Image.open(uploaded_file).convert("RGB")
    image = image.resize((224, 224))

    img_array = np.array(image).astype("float32")
    img_array = np.expand_dims(img_array, axis=0)

    return image, img_array



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
        st.session_state.akg_fiber = default_akg["fiber"]
        st.session_state.akg_calcium = default_akg["calcium"]
        st.session_state.akg_iron = default_akg["iron"]
        st.session_state.akg_vitamin_c = default_akg["vitamin_c"]


# =========================
# DATA FUNCTIONS
# =========================
@st.cache_data
def load_data(csv_path: Path) -> pd.DataFrame:
    return pd.read_csv(csv_path)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    column_map = {
        "foodname": "name",
        "food_name": "name",
        "foodname_100g": "name",
        "nama_makanan": "name",
        "class_name": "name",

        "calories_kcal": "calories",
        "protein_g": "protein",
        "fat_g": "fat",
        "carbs_g": "carbs",

        "fiber_g": "fiber",
        "calcium_mg": "calcium",
        "iron_mg": "iron",
        "vitamin_c_mg": "vitamin_c",

        "total_fat": "fat",
        "lemak": "fat",
        "carbohydrates": "carbs",
        "carbohydrate": "carbs",
        "karbohidrat": "carbs",
    }

    df = df.copy()
    df.columns = [col.strip() for col in df.columns]
    df = df.rename(columns={col: column_map.get(col, col) for col in df.columns})

    return df


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    df = standardize_columns(df)

    required_columns = [
        "name",
        "calories",
        "protein",
        "fat",
        "carbs",
        "fiber",
        "calcium",
        "iron",
        "vitamin_c",
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        st.error(f"Missing required columns: {missing_columns}")
        st.stop()

    nutrition_columns = [
        "calories",
        "protein",
        "fat",
        "carbs",
        "fiber",
        "calcium",
        "iron",
        "vitamin_c",
    ]

    for col in nutrition_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["name"] = df["name"].astype(str).str.strip()

    df = df.dropna(subset=["name"] + nutrition_columns)
    df = df[df["name"] != ""].copy()

    df = df[
        (df["calories"] > 0) &
        (df["protein"] >= 0) &
        (df["fat"] >= 0) &
        (df["carbs"] >= 0) &
        (df["fiber"] >= 0) &
        (df["calcium"] >= 0) &
        (df["iron"] >= 0) &
        (df["vitamin_c"] >= 0)
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
    fiber = float(base_row["fiber"])
    calcium = float(base_row["calcium"])
    iron = float(base_row["iron"])
    vitamin_c = float(base_row["vitamin_c"])

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
            fiber += float(extra_row["fiber"])
            calcium += float(extra_row["calcium"])
            iron += float(extra_row["iron"])
            vitamin_c += float(extra_row["vitamin_c"])

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
            fiber += float(extra_row["fiber"])
            calcium += float(extra_row["calcium"])
            iron += float(extra_row["iron"])
            vitamin_c += float(extra_row["vitamin_c"])

    return {
    "calories": int(round(calories)),
    "protein": int(round(protein)),
    "fat": round(fat, 1),
    "carbs": int(round(carbs)),
    "fiber": round(fiber, 1),
    "calcium": round(calcium, 1),
    "iron": round(iron, 1),
    "vitamin_c": round(vitamin_c, 1)
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
    fiber = row["fiber"] * portion_gram / 100
    calcium = row["calcium"] * portion_gram / 100
    iron = row["iron"] * portion_gram / 100
    vitamin_c = row["vitamin_c"] * portion_gram / 100

    return calories, protein, fat, carbs, fiber, calcium, iron, vitamin_c


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
        "CSV file was not found. Put `nutrition_table_cleaned.csv` inside the `data` folder."
    )
    st.stop()

raw_df = prepare_data(
    load_data(DATA_PATH)
)

food_model = load_food_model(MODEL_PATH)

if (
    "working_df" not in st.session_state
    or set(st.session_state.working_df.columns) != set(raw_df.columns)
):
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
        "Apply Profile",
        type="primary"
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
    st.session_state.akg_fiber = estimated_akg["fiber"]
    st.session_state.akg_calcium = estimated_akg["calcium"]
    st.session_state.akg_iron = estimated_akg["iron"]
    st.session_state.akg_vitamin_c = estimated_akg["vitamin_c"]

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
        <div class="hero-title">Food Nutrition Dashboard</div>
        <div class="hero-subtitle">
            This dashboard presents food nutrition data, including calories,
            protein, fat, carbohydrates, portion analysis, daily nutrition needs,
            and food tracking summary.
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
    total_fiber = 0
    total_calcium = 0
    total_iron = 0
    total_vitamin_c = 0

else:
    total_calories = meal_df["Calories"].sum()
    total_protein = meal_df["Protein"].sum()
    total_fat = meal_df["Fat"].sum()
    total_carbs = meal_df["Carbohydrates"].sum()
    total_fiber = meal_df["Fiber"].sum()
    total_calcium = meal_df["Calcium"].sum()
    total_iron = meal_df["Iron"].sum()
    total_vitamin_c = meal_df["Vitamin C"].sum()

# SVG CONFIG
SVG_CONFIG = {
    "male": {
        "scale": 1,
        "top": -90,
        "left": -15,
        "body_height": 500
    },
    "female": {
        "scale": 1,
        "top": -57,
        "left": 180,
        "body_height": 480
    }, 
    "child": {
        "scale": 0.9,
        "top": -227,
        "left": -150,
        "body_height": 450
    }
}


def get_svg_path(age, gender):
    if age < 10:
        return ASSETS_DIR / "child.svg", "child"

    if gender == "Male":
        return ASSETS_DIR / "male.svg", "male"

    return ASSETS_DIR / "female.svg", "female"


def load_svg(svg_path: Path):
    if not svg_path.exists():
        return ""

    with open(svg_path, "r", encoding="utf-8") as f:
        svg = f.read()

    svg = svg.replace(
        "<svg",
        """
        <svg
            width="300%"
            height="160%"
            viewBox="0 0 512 512"
            preserveAspectRatio="xMidYMid meet"
        """
    )

    return svg


def generate_body_progress(svg_content, percent, body_type):
    cfg = SVG_CONFIG[body_type]

    percent = max(0, min(percent, 100))
    body_height = cfg["body_height"]
    fill_px = (percent / 100) * body_height

    return f"""
    <div style="
        position:relative;
        width:320px;
        height:520px;
        margin:auto;
        overflow:hidden;
    ">
        <div style="
            position:absolute;
            bottom:0;
            left:50%;
            transform:translateX(-50%);
            width:300px;
            height:{fill_px}px;
            background:#4ade80;
            z-index:1;
            border-radius:10px;
        "></div>

        <div style="
            position:absolute;
            top:{cfg["top"]}px;
            left:{cfg["left"]}px;
            transform:
                translateX(-50%)
                scale({cfg["scale"]});
            z-index:5;
            width:220px;
            height:500px;
        ">
            {svg_content}
        </div>
    </div>
    """
# =========================
# BODY NUTRITION PROGRESS
# =========================
st.markdown("## Body Nutrition Progress")

calories_pct = min(
    (total_calories / st.session_state.akg_calories) * 100,
    100
)

protein_pct = min(
    (total_protein / st.session_state.akg_protein) * 100,
    100
)

fat_pct = min(
    (total_fat / st.session_state.akg_fat) * 100,
    100
)

carbs_pct = min(
    (total_carbs / st.session_state.akg_carbs) * 100,
    100
)

fiber_pct = min(
    (total_fiber / st.session_state.akg_fiber) * 100,
    100
)

calcium_pct = min(
    (total_calcium / st.session_state.akg_calcium) * 100,
    100
)

iron_pct = min(
    (total_iron / st.session_state.akg_iron) * 100,
    100
)

vitamin_c_pct = min(
    (total_vitamin_c / st.session_state.akg_vitamin_c) * 100,
    100
)

overall_pct = (
    calories_pct +
    protein_pct +
    fat_pct +
    carbs_pct +
    fiber_pct +
    calcium_pct +
    iron_pct +
    vitamin_c_pct
) / 8

svg_path, body_type = get_svg_path(
    st.session_state.age,
    st.session_state.gender
)

svg_content = load_svg(svg_path)

body_col, progress_col = st.columns([1, 1.4])

with body_col:
    if svg_content:
        components.html(
            generate_body_progress(
                svg_content,
                overall_pct,
                body_type
            ),
            height=540
        )
    else:
        st.warning("Body SVG asset was not found.")

with progress_col:
    st.markdown("### Daily Fulfillment")

    st.write(
        f"Calories: {total_calories:.2f} / "
        f"{st.session_state.akg_calories:.2f} kcal "
        f"({calories_pct:.1f}%)"
    )
    st.progress(calories_pct / 100)

    st.write(
        f"Protein: {total_protein:.2f} / "
        f"{st.session_state.akg_protein:.2f} g "
        f"({protein_pct:.1f}%)"
    )
    st.progress(protein_pct / 100)

    st.write(
        f"Fat: {total_fat:.2f} / "
        f"{st.session_state.akg_fat:.2f} g "
        f"({fat_pct:.1f}%)"
    )
    st.progress(fat_pct / 100)

    st.write(
        f"Carbohydrates: {total_carbs:.2f} / "
        f"{st.session_state.akg_carbs:.2f} g "
        f"({carbs_pct:.1f}%)"
    )
    st.progress(carbs_pct / 100)

    st.write(
        f"Fiber: {total_fiber:.2f} / "
        f"{st.session_state.akg_fiber:.2f} g "
        f"({fiber_pct:.1f}%)"
    )
    st.progress(fiber_pct / 100)

    st.write(
        f"Calcium: {total_calcium:.2f} / "
        f"{st.session_state.akg_calcium:.2f} mg "
        f"({calcium_pct:.1f}%)"
    )
    st.progress(calcium_pct / 100)

    st.write(
        f"Iron: {total_iron:.2f} / "
        f"{st.session_state.akg_iron:.2f} mg "
        f"({iron_pct:.1f}%)"
    )
    st.progress(iron_pct / 100)

    st.write(
        f"Vitamin C: {total_vitamin_c:.2f} / "
        f"{st.session_state.akg_vitamin_c:.2f} mg "
        f"({vitamin_c_pct:.1f}%)"
    )
    st.progress(vitamin_c_pct / 100)

    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">Overall Nutrition Progress</div>
            <div class="insight-text">
                Your overall nutrition fulfillment today is
                <b>{overall_pct:.1f}%</b>.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# ADDED FOOD TODAY
# =========================
st.markdown("## Added Food Today")
st.caption(
    "Add your food manually or upload a food image to track today's nutrition intake."
)

input_method = st.radio(
    "Choose input method",
    ["Search food manually", "Upload food image"],
    horizontal=True
)

selected_food_name = None
selected_food_row = None

if input_method == "Search food manually":
    add_col1, add_col2, add_col3 = st.columns([2, 1, 1])

    with add_col1:
        selected_food_name = st.selectbox(
            "Choose food",
            filtered_df["name"].sort_values().unique(),
            key="manual_add_food"
        )

    with add_col2:
        add_portion = st.number_input(
            "Portion (grams)",
            min_value=1,
            max_value=3000,
            value=100,
            step=10,
            key="manual_add_portion"
        )

    selected_food_row = filtered_df[
        filtered_df["name"] == selected_food_name
    ].iloc[0]

    add_calories, add_protein, add_fat, add_carbs, add_fiber, add_calcium, add_iron, add_vitamin_c = calculate_food_nutrition(
        selected_food_row,
        add_portion
    )

    with add_col3:
        st.write("")
        st.write("")

        if st.button("Add Food Today", type="primary", key="manual_add_button"):
            st.session_state.meal_log.append(
                {
                    "Food": selected_food_name,
                    "Portion (g)": add_portion,
                    "Calories": round(add_calories, 2),
                    "Protein": round(add_protein, 2),
                    "Fat": round(add_fat, 2),
                    "Carbohydrates": round(add_carbs, 2),
                    "Fiber": round(add_fiber, 2),
                    "Calcium": round(add_calcium, 2),
                    "Iron": round(add_iron, 2),
                    "Vitamin C": round(add_vitamin_c, 2)
                }
            )

            st.rerun()

else:
    upload_col1, upload_col2, upload_col3 = st.columns([2, 1, 1])

    with upload_col1:
        uploaded_food_image = st.file_uploader(
            "Upload food image",
            type=["jpg", "jpeg", "png"],
            key="uploaded_food_image"
        )

    with upload_col2:
        image_portion = st.number_input(
            "Portion (grams)",
            min_value=1,
            max_value=3000,
            value=100,
            step=10,
            key="image_add_portion"
        )

    if uploaded_food_image is not None:
        image_preview, img_array = preprocess_uploaded_image(uploaded_food_image)

        st.image(
            image_preview,
            caption="Uploaded food image",
            use_container_width=280
        )

        prediction = food_model.predict(img_array, verbose=0)


        if isinstance(prediction, dict):
            if "class_output" in prediction:
                class_probs = prediction["class_output"]
            elif "classification_output" in prediction:
                class_probs = prediction["classification_output"]
            elif "food_output" in prediction:
                class_probs = prediction["food_output"]
            else:
                st.error(
                    "Model tidak mengeluarkan output class makanan. "
                    "Yang tersedia hanya: " + ", ".join(prediction.keys())
                )
                st.stop()

        elif isinstance(prediction, (list, tuple)):
            class_probs = prediction[0]

        else:
            class_probs = prediction

        class_probs = np.array(class_probs)

        if class_probs.ndim == 1:
            class_probs = np.expand_dims(class_probs, axis=0)

        if class_probs.shape[-1] != len(FOOD101_CLASSES):
            st.error(
                f"Model output berjumlah {class_probs.shape[-1]}, "
                f"sedangkan FOOD101_CLASSES berjumlah {len(FOOD101_CLASSES)}. "
                "Berarti output ini bukan probabilitas class FOOD101."
            )
            st.stop()

        predicted_index = int(np.argmax(class_probs[0]))
        confidence = float(np.max(class_probs[0]) * 100)

        predicted_food_class = FOOD101_CLASSES[predicted_index]
        predicted_food_name = predicted_food_class.replace("_", " ")

        st.success(
            f"Detected food: {predicted_food_name.title()} "
            f"({confidence:.1f}% confidence)"
        )

        normalized_predicted_name = predicted_food_name.lower()

        matched_food = filtered_df[
            filtered_df["name"]
            .str.lower()
            .str.replace("_", " ", regex=False)
            .eq(normalized_predicted_name)
        ]

        if matched_food.empty:
            matched_food = filtered_df[
                filtered_df["name"]
                .str.lower()
                .str.replace("_", " ", regex=False)
                .str.contains(normalized_predicted_name, regex=False, na=False)
            ]

        if matched_food.empty:
            st.warning(
                f"Food '{predicted_food_name.title()}' was detected, "
                "but it was not found in the nutrition dataset."
            )
        else:
            selected_food_row = matched_food.iloc[0]
            selected_food_name = str(selected_food_row["name"]).replace("_", " ").title()

            add_calories, add_protein, add_fat, add_carbs, add_fiber, add_calcium, add_iron, add_vitamin_c = calculate_food_nutrition(
                selected_food_row,
                image_portion
            )

            with upload_col3:
                st.write("")
                st.write("")

                if st.button("Add Detected Food", type="primary", key="image_add_button"):
                    st.session_state.meal_log.append(
                        {
                            "Food": selected_food_name,
                            "Portion (g)": image_portion,
                            "Calories": round(add_calories, 2),
                            "Protein": round(add_protein, 2),
                            "Fat": round(add_fat, 2),
                            "Carbohydrates": round(add_carbs, 2),
                            "Fiber": round(add_fiber, 2),
                            "Calcium": round(add_calcium, 2),
                            "Iron": round(add_iron, 2),
                            "Vitamin C": round(add_vitamin_c, 2)
                        }
                    )

                    st.rerun()

# =========================
# FOOD LOG TABLE
# =========================
st.markdown("## Food Log Table")

meal_df = pd.DataFrame(st.session_state.meal_log)

if meal_df.empty:
    st.warning("No food has been added today.")

else:
    rows_html = ""

    for _, row in meal_df.iterrows():
        food_name = html.escape(str(row["Food"]))

        rows_html += f'''<tr>
<td class="food-name-cell">{food_name}</td>
<td>{float(row["Portion (g)"]):.0f} g</td>
<td>{float(row["Calories"]):.1f} kcal</td>
<td>{float(row["Protein"]):.1f} g</td>
<td>{float(row["Fat"]):.1f} g</td>
<td>{float(row["Carbohydrates"]):.1f} g</td>
<td>{float(row["Fiber"]):.1f} g</td>
<td>{float(row["Calcium"]):.1f} mg</td>
<td>{float(row["Iron"]):.1f} mg</td>
<td>{float(row["Vitamin C"]):.1f} mg</td>
</tr>'''

    table_html = f'''<div class="food-log-wrapper">
<table class="food-log-table">
<thead>
<tr>
<th>Food</th>
<th>Portion</th>
<th>Calories</th>
<th>Protein</th>
<th>Fat</th>
<th>Carbohydrates</th>
<th>Fiber</th>
<th>Calcium</th>
<th>Iron</th>
<th>Vitamin C</th>
</tr>
</thead>
<tbody>
{rows_html}
</tbody>
</table>
</div>'''

    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("### Manage Food Log")

    action_col1, action_col2, action_col3 = st.columns([2, 1, 1])

    with action_col1:
        food_options = meal_df["Food"].unique().tolist()

        selected_delete_food = st.selectbox(
            "Select food to delete",
            food_options,
            key="selected_delete_food"
        )

    with action_col2:
        st.write("")
        st.write("")

        if st.button("Delete Food", type="secondary", use_container_width=True):
            st.session_state.meal_log = [
                food for food in st.session_state.meal_log
                if food["Food"] != selected_delete_food
            ]

            st.rerun()

    with action_col3:
        st.write("")
        st.write("")

        if st.button("Clear All", type="secondary", use_container_width=True):
            st.session_state.meal_log = []

            st.rerun()

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

check_calories, check_protein, check_fat, check_carbs, check_fiber, check_calcium, check_iron, check_vitamin_c = calculate_food_nutrition(
    check_row,
    check_portion
)

st.markdown(
    f"### Nutrition content for {check_portion} g of {check_food}"
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

calories_pct_check = (check_calories / st.session_state.akg_calories) * 100
protein_pct_check = (check_protein / st.session_state.akg_protein) * 100
fat_pct_check = (check_fat / st.session_state.akg_fat) * 100
carbs_pct_check = (check_carbs / st.session_state.akg_carbs) * 100
fiber_pct_check = (check_fiber / st.session_state.akg_fiber) * 100
calcium_pct_check = (check_calcium / st.session_state.akg_calcium) * 100
iron_pct_check = (check_iron / st.session_state.akg_iron) * 100
vitamin_c_pct_check = (check_vitamin_c / st.session_state.akg_vitamin_c) * 100

checker_result_html = f'''<div class="checker-result-grid">
<div class="checker-result-card">
<div class="checker-label">Calories</div>
<div class="checker-value">{check_calories:.2f}</div>
<div class="checker-unit">kcal</div>
<div class="checker-percent">{calories_pct_check:.1f}% of daily need</div>
</div>

<div class="checker-result-card">
<div class="checker-label">Protein</div>
<div class="checker-value">{check_protein:.2f}</div>
<div class="checker-unit">g</div>
<div class="checker-percent">{protein_pct_check:.1f}% of daily need</div>
</div>

<div class="checker-result-card">
<div class="checker-label">Fat</div>
<div class="checker-value">{check_fat:.2f}</div>
<div class="checker-unit">g</div>
<div class="checker-percent">{fat_pct_check:.1f}% of daily need</div>
</div>

<div class="checker-result-card">
<div class="checker-label">Carbohydrates</div>
<div class="checker-value">{check_carbs:.2f}</div>
<div class="checker-unit">g</div>
<div class="checker-percent">{carbs_pct_check:.1f}% of daily need</div>
</div>

<div class="checker-result-card">
<div class="checker-label">Fiber</div>
<div class="checker-value">{check_fiber:.2f}</div>
<div class="checker-unit">g</div>
<div class="checker-percent">{fiber_pct_check:.1f}% of daily need</div>
</div>

<div class="checker-result-card">
<div class="checker-label">Calcium</div>
<div class="checker-value">{check_calcium:.2f}</div>
<div class="checker-unit">mg</div>
<div class="checker-percent">{calcium_pct_check:.1f}% of daily need</div>
</div>

<div class="checker-result-card">
<div class="checker-label">Iron</div>
<div class="checker-value">{check_iron:.2f}</div>
<div class="checker-unit">mg</div>
<div class="checker-percent">{iron_pct_check:.1f}% of daily need</div>
</div>

<div class="checker-result-card">
<div class="checker-label">Vitamin C</div>
<div class="checker-value">{check_vitamin_c:.2f}</div>
<div class="checker-unit">mg</div>
<div class="checker-percent">{vitamin_c_pct_check:.1f}% of daily need</div>
</div>
</div>'''

st.markdown(checker_result_html, unsafe_allow_html=True)

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
    hover_data=["calories", "protein", "fat", "carbs", "fiber", "calcium", "iron", "vitamin_c"],
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

st.warning(
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

col5, col6 = st.columns(2)

with col5:
    fig_fiber = px.histogram(
        filtered_df,
        x="fiber",
        nbins=30,
        color_discrete_sequence=["#A7E8B8"],
        title="Fiber Distribution"
    )

    st.plotly_chart(
        apply_plot_theme(fig_fiber),
        use_container_width=True
    )

with col6:
    fig_calcium = px.histogram(
        filtered_df,
        x="calcium",
        nbins=30,
        color_discrete_sequence=["#8EDFA8"],
        title="Calcium Distribution"
    )

    st.plotly_chart(
        apply_plot_theme(fig_calcium),
        use_container_width=True
    )

col7, col8 = st.columns(2)

with col7:
    fig_iron = px.histogram(
        filtered_df,
        x="iron",
        nbins=30,
        color_discrete_sequence=["#72D591"],
        title="Iron Distribution"
    )

    st.plotly_chart(
        apply_plot_theme(fig_iron),
        use_container_width=True
    )

with col8:
    fig_vitamin_c = px.histogram(
        filtered_df,
        x="vitamin_c",
        nbins=30,
        color_discrete_sequence=["#BCEBCB"],
        title="Vitamin C Distribution"
    )

    st.plotly_chart(
        apply_plot_theme(fig_vitamin_c),
        use_container_width=True
    )

# =========================
# INSIGHTS
# =========================
st.markdown("## Key Insights")

avg_cal = filtered_df["calories"].mean()
avg_protein = filtered_df["protein"].mean()
median_eff = filtered_df["overall_portions_combined"].median()

# Insight from Check Food Nutrition by Portion
nutrition_percentages = {
    "Calories": calories_pct_check,
    "Protein": protein_pct_check,
    "Fat": fat_pct_check,
    "Carbohydrates": carbs_pct_check,
    "Fiber": fiber_pct_check,
    "Calcium": calcium_pct_check,
    "Iron": iron_pct_check,
    "Vitamin C": vitamin_c_pct_check
}

highest_nutrient = max(
    nutrition_percentages,
    key=nutrition_percentages.get
)

lowest_nutrient = min(
    nutrition_percentages,
    key=nutrition_percentages.get
)

highest_value = nutrition_percentages[highest_nutrient]
lowest_value = nutrition_percentages[lowest_nutrient]

if calories_pct_check >= 25:
    calorie_insight = (
        "This portion contributes quite a high amount of daily calories, "
        "so it is better to balance it with lower-calorie foods in other meals."
    )
elif calories_pct_check >= 10:
    calorie_insight = (
        "This portion gives a moderate calorie contribution and can fit well "
        "as part of a balanced meal."
    )
else:
    calorie_insight = (
        "This portion has a relatively low calorie contribution, so it may need "
        "to be combined with other foods to meet daily energy needs."
    )

if protein_pct_check >= 20:
    protein_insight = (
        "The protein contribution is relatively strong for this portion."
    )
elif protein_pct_check >= 10:
    protein_insight = (
        "The protein contribution is moderate for this portion."
    )
else:
    protein_insight = (
        "The protein contribution is relatively low, so adding a protein-rich food "
        "could make the meal more balanced."
    )

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

    <div class="insight-card">
        <div class="insight-title">Main nutrient contribution</div>
        <div class="insight-text">
            For <b>{check_portion} g of {check_food}</b>, the highest daily-need contribution
            comes from <b>{highest_nutrient}</b>, reaching <b>{highest_value:.1f}%</b>
            of the daily requirement.
        </div>
    </div>

    <div class="insight-card">
        <div class="insight-title">Lowest nutrient contribution</div>
        <div class="insight-text">
            The lowest contribution from this portion is <b>{lowest_nutrient}</b>,
            at only <b>{lowest_value:.1f}%</b> of the daily need.
            This nutrient may need to be supported by other foods in the same day.
        </div>
    </div>

    <div class="insight-card">
        <div class="insight-title">Portion recommendation</div>
        <div class="insight-text">
            {calorie_insight}
            {protein_insight}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)