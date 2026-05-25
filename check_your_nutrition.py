# check_your_nutrition.py
import base64
from pathlib import Path
import streamlit.components.v1 as components
import pandas as pd
import streamlit as st


# PATH
BASE_DIR = Path(__file__).resolve().parent

ASSETS_DIR = BASE_DIR / "assets"

AKG_PATH = BASE_DIR / "data" / "akg.csv"

# LOAD AKG
@st.cache_data
def load_akg():
    return pd.read_csv(AKG_PATH)


# LOAD CSS
def load_css():

    css_path = BASE_DIR / "styles" / "style.css"

    if css_path.exists():

        with open(css_path) as f:
            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )


# SELECT SVG
def get_svg_path(age, gender):

    if age < 10:
        return ASSETS_DIR / "child.svg", "child"

    if gender == "Male":
        return ASSETS_DIR / "male.svg", "male"

    return ASSETS_DIR / "female.svg", "female"

# LOAD SVG
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

# BODY PROGRESS SVG
def generate_body_progress(svg_content, percent, body_type):

    cfg = SVG_CONFIG[body_type]

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

        <!-- HIJAU -->
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

        <!-- SVG -->
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
    return html

# FIND AKG TARGET
def get_akg_targets(
    akg_df,
    gender,
    age,
    condition,
    trimester,
    breastfeeding_phase
):

    # CHILD
    if age < 10:

        filtered = akg_df[
            (akg_df["age_category"] == "infants_children")
            &
            (akg_df["min_age"] <= age)
            &
            (akg_df["max_age"] >= age)
        ]

    else:

        filtered = akg_df[
            (akg_df["age_category"] == gender.lower())
            &
            (akg_df["min_age"] <= age)
            &
            (akg_df["max_age"] >= age)
        ]

    if filtered.empty:

        return {
            "calories": 2000,
            "protein": 60,
            "fat": 65,
            "carbs": 300
        }

    base = filtered.iloc[0]

    calories = float(base["calories"])
    protein = float(base["protein"])
    fat = float(base["total_fat"])
    carbs = float(base["carbohydrates"])

    # PREGNANT
    if condition == "Pregnant":

        if trimester == "Trimester 1":
            preg = akg_df[
                akg_df["age_category"] == "pregnant"
            ]

            preg = preg[preg["age_group"] == "trimester 1"]

        elif trimester == "Trimester 2":

            preg = akg_df[
                akg_df["age_category"] == "pregnant"
            ]

            preg = preg[preg["age_group"] == "trimester 2"]

        else:

            preg = akg_df[
                akg_df["age_category"] == "pregnant"
            ]

            preg = preg[preg["age_group"] == "trimester 3"]

        if not preg.empty:

            preg = preg.iloc[0]

            calories += float(preg["calories"])
            protein += float(preg["protein"])
            fat += float(preg["total_fat"])
            carbs += float(preg["carbohydrates"])

    # BREASTFEEDING
    elif condition == "Breastfeeding":

        if breastfeeding_phase == "First 6 Months":

            bf = akg_df[
                akg_df["age_category"] == "breastfeeding"
            ]

            bf = bf[bf["age_group"] == "first 6 months"]

        else:

            bf = akg_df[
                akg_df["age_category"] == "breastfeeding"
            ]

            bf = bf[bf["age_group"] == "second 6 months"]

        if not bf.empty:

            bf = bf.iloc[0]

            calories += float(bf["calories"])
            protein += float(bf["protein"])
            fat += float(bf["total_fat"])
            carbs += float(bf["carbohydrates"])

    return {
        "calories": calories,
        "protein": protein,
        "fat": fat,
        "carbs": carbs
    }

#Main Page
def show_check_your_nutrition(df):

    akg_df = load_akg()

    load_css()

    # SESSION STATE
    if "nutrition_foods" not in st.session_state:
        st.session_state.nutrition_foods = []

    # SIDEBAR
    st.sidebar.title("Nutrition Profile")

    gender = st.sidebar.selectbox(
        "Gender",
        [
            "Male",
            "Female"
        ]
    )

    age = st.sidebar.slider(
        "Age",
        0,
        100,
        21
    )

    trimester = None
    breastfeeding_phase = None
    condition = "None"

    if gender == "Female":

        condition = st.sidebar.selectbox(
            "Special Condition",
            [
                "None",
                "Pregnant",
                "Breastfeeding"
            ]
        )

        if condition == "Pregnant":

            trimester = st.sidebar.selectbox(
                "Pregnancy Trimester",
                [
                    "Trimester 1",
                    "Trimester 2",
                    "Trimester 3"
                ]
            )

        elif condition == "Breastfeeding":

            breastfeeding_phase = st.sidebar.selectbox(
                "Breastfeeding Phase",
                [
                    "First 6 Months",
                    "After 6 Months"
                ]
            )

    # TARGETS
    targets = get_akg_targets(
        akg_df,
        gender,
        age,
        condition,
        trimester,
        breastfeeding_phase
    )

    target_calories = targets["calories"]
    target_protein = targets["protein"]
    target_fat = targets["fat"]
    target_carbs = targets["carbs"]

    # TOTAL NUTRITION
    total_calories = 0
    total_protein = 0
    total_fat = 0
    total_carbs = 0

    for food in st.session_state.nutrition_foods:

        total_calories += float(food["calories"])
        total_protein += float(food["protein"])
        total_fat += float(food["fat"])
        total_carbs += float(food["carbs"])

    # PERCENTAGES NUTRITIONS
    calories_pct = min(
        (total_calories / target_calories) * 100,
        100
    )

    protein_pct = min(
        (total_protein / target_protein) * 100,
        100
    )

    fat_pct = min(
        (total_fat / target_fat) * 100,
        100
    )

    carbs_pct = min(
        (total_carbs / target_carbs) * 100,
        100
    )

    overall_pct = (
        calories_pct +
        protein_pct +
        fat_pct +
        carbs_pct
    ) / 4

    # HEADER
    st.title("Check Your Nutrition")

    st.caption(
        "Track your daily nutrition intake "
        "using food recommendations and "
        "dynamic AKG targets."
    )

    # BODY  PROGRESS
    svg_path, body_type = get_svg_path(age, gender)

    svg_content = load_svg(svg_path)

    col1, col2 = st.columns([1, 1])

    with col1:
        components.html(
        generate_body_progress(
            svg_content,
            overall_pct,
            body_type
        ),
        height=540
    )

    with col2:

        st.markdown("## Nutrition Progress")

        st.write(
            f"Calories "
            f"({total_calories:.1f} / "
            f"{target_calories:.1f} kcal)"
        )

        st.progress(calories_pct / 100)

        st.write(
            f"{calories_pct:.1f}% fulfilled"
        )

        st.markdown("---")

        st.write(
            f"Protein "
            f"({total_protein:.1f} / "
            f"{target_protein:.1f} g)"
        )

        st.progress(protein_pct / 100)

        st.write(
            f"{protein_pct:.1f}% fulfilled"
        )

        st.markdown("---")

        st.write(
            f"Fat "
            f"({total_fat:.1f} / "
            f"{target_fat:.1f} g)"
        )

        st.progress(fat_pct / 100)

        st.write(
            f"{fat_pct:.1f}% fulfilled"
        )

        st.markdown("---")

        st.write(
            f"Carbohydrates "
            f"({total_carbs:.1f} / "
            f"{target_carbs:.1f} g)"
        )

        st.progress(carbs_pct / 100)

        st.write(
            f"{carbs_pct:.1f}% fulfilled"
        )

    # SEARCH FOOD
    st.markdown("## Add Foods")

    search = st.text_input(
        "Search food from dataset"
    )

    if search:

        result_df = df[
            df["name"].str.contains(
                search,
                case=False,
                na=False
            )
        ].copy()

        result_df = result_df.head(10)

        if result_df.empty:

            st.warning("No food found.")

        else:

            for idx, row in result_df.iterrows():

                with st.container(border=True):
                    left_col, right_col = st.columns([10, 2])

                    with left_col:

                        # FOOD NAME
                        st.markdown(
                            f"""
                            <div class="food-title">
                                {row['name']}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # NUTRITION SECTION
                        nutrition_area, empty_space = st.columns([6, 6])

                        with nutrition_area:

                            nutrition_cols = st.columns(4)

                            # CALORIES
                            with nutrition_cols[0]:

                                st.markdown(
                                    f"""
                                    <div class="nutrition-card-calories">
                                        🔥<br>
                                        {row['calories']} kcal
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                            # PROTEIN
                            with nutrition_cols[1]:

                                st.markdown(
                                    f"""
                                    <div class="nutrition-card-protein">
                                        💪<br>
                                        {row['protein']}g
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                            # FAT
                            with nutrition_cols[2]:

                                st.markdown(
                                    f"""
                                    <div class="nutrition-card-fat">
                                        🧈<br>
                                        {row['fat']}g
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                            # CARBS
                            with nutrition_cols[3]:

                                st.markdown(
                                    f"""
                                    <div class="nutrition-card-carbs">
                                        🍞<br>
                                        {row['carbs']}g
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                    # Tombol Add
                    with right_col:

                        top_space, button_space, bottom_space = st.columns([1, 4, 1])

                        with button_space:

                            st.markdown(
                                """
                                <div class="delete-button-space"></div>
                                """,
                                unsafe_allow_html=True
                            )

                            if st.button(
                                "Add",
                                key=f"add_{idx}",
                                use_container_width=True
                            ):

                                st.session_state.nutrition_foods.append(
                                    row.to_dict()
                                )

                                st.rerun()


    # Added Food
    st.markdown("## Added Foods")

    if len(st.session_state.nutrition_foods) == 0:

        st.info("No foods added yet.")

    else:

        for i, food in enumerate(
            st.session_state.nutrition_foods
        ):

            with st.container(border=True):
                left_col, right_col = st.columns([10, 2])

                with left_col:

                    # FOOD NAME
                    st.markdown(
                        f"""
                        <div class="food-title-added">
                            {food['name']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # NUTRITION SECTION
                    nutrition_area, empty_space = st.columns([6, 6])

                    with nutrition_area:

                        nutrition_cols = st.columns(4)

                        # CALORIES
                        with nutrition_cols[0]:

                            st.markdown(
                                f"""
                                <div class="nutrition-card-calories">
                                    🔥<br>
                                    {food['calories']} kcal
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        # PROTEIN
                        with nutrition_cols[1]:

                            st.markdown(
                                f"""
                                <div class="nutrition-card-protein">
                                    💪<br>
                                    {food['protein']}g
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        # FAT
                        with nutrition_cols[2]:

                            st.markdown(
                                f"""
                                <div class="nutrition-card-fat">
                                    🧈<br>
                                    {food['fat']}g
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        # CARBS
                        with nutrition_cols[3]:

                            st.markdown(
                                f"""
                                <div class="nutrition-card-carbs">
                                    🍞<br>
                                    {food['carbs']}g
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                # Tombol Delete
                with right_col:

                    top_space, button_space, bottom_space = st.columns([1, 4, 1])

                    with button_space:

                        st.markdown(
                            """
                            <div class="delete-button-space"></div>
                            """,
                            unsafe_allow_html=True
                        )

                        if st.button(
                            "Delete",
                            key=f"delete_{i}",
                            use_container_width=True
                        ):

                            st.session_state.nutrition_foods.pop(i)

                            st.rerun()