# nutrition-dashboard

# Food Nutrition Dashboard

Food Nutrition Dashboard is an interactive Streamlit-based dashboard designed to help users explore food nutrition data, check nutrition values by portion size, track daily food intake, and compare consumed nutrients with daily nutrition needs based on AKG standards.

This project combines food nutrition datasets, AKG data, and a machine learning model for food image detection to support daily nutrition monitoring in a simple and interactive way.

---

## Features

- User profile input based on age, gender, and special condition
- Daily nutrition needs calculation based on AKG data
- Food search and nutrition checking by portion size
- Food log for tracking daily food intake
- Daily nutrition fulfillment progress
- Food image upload and food detection using a machine learning model
- Nutrition visualization using interactive charts
- Nutrient distribution analysis
- Key insights based on selected food and daily nutrition progress

---

## Project Objectives

The main objectives of this project are:

1. To process and integrate food nutrition data with AKG standards.
2. To build an interactive dashboard for monitoring daily nutrition intake.
3. To calculate nutrition values based on food portion size.
4. To apply a machine learning model for food image detection.
5. To provide simple insights related to daily nutrition fulfillment.

---

## Dataset Sources

This project uses several nutrition-related datasets:

### 1. AKG Dataset

The AKG dataset is based on:

- Peraturan Menteri Kesehatan Republik Indonesia Nomor 28 Tahun 2019
- Angka Kecukupan Gizi yang Dianjurkan untuk Masyarakat Indonesia

The dataset is used to estimate daily nutrition needs based on:

- age
- gender
- pregnancy condition
- breastfeeding condition

### 2. Food101 Dataset

The Food101 dataset is used as the basis for food image classification. It contains 101 food categories and is used to support the image-based food detection feature.

---

## Main Nutrients Used

The dashboard focuses on the following nutrients:

- Calories
- Protein
- Fat
- Carbohydrates
- Fiber
- Calcium
- Iron
- Vitamin C

---

## Technologies Used

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- Pillow
- TensorFlow
- Keras
- HTML/CSS

---

## Project Structure

```text
nutrition-dashboard/
│
├── app.py
├── requirements.txt
├── runtime.txt
├── README.md
│
├── data/
│   ├── akg.csv
│   └── nutrition_table_cleaned.csv
│
├── models/
│   └── best_nutrivision_cnn_food101_akg.keras
│
├── assets/
│   ├── male.svg
│   ├── female.svg
│   └── child.svg
│
└── styles/
    └── style.css

## Installation

Clone this repository:

```bash
git clone https://github.com/broomrun/nutrition-dashboard.git
cd nutrition-dashboard
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

For Windows:

```bash
.venv\Scripts\activate
```

For macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the App Locally

Run the Streamlit app using:

```bash
streamlit run app.py
```

After running the command, the dashboard will open in your browser.

## Deployment

This project can be deployed using **Streamlit Community Cloud**.

Recommended deployment settings:

* **Main file path:** `app.py`
* **Python version:** `3.13`
* **Dependencies:** listed in `requirements.txt`

## How the Dashboard Works

1. The user enters their profile information in the sidebar.
2. The dashboard calculates daily nutrition needs using AKG data.
3. The user can search food manually or upload a food image.
4. Nutrition values are calculated based on portion size.
5. Added foods are stored in the food log.
6. The dashboard compares total consumed nutrients with daily needs.
7. Visualizations and insights are displayed to support interpretation.

## Machine Learning Model

The machine learning model is used to detect food categories from uploaded images. The detected food class is then matched with the nutrition dataset to estimate its nutrition content.

Model file:

```text
models/best_nutrivision_cnn_food101_akg.keras
```

## Notes

* Nutrition values are calculated based on available dataset values and portion size.
* Food image detection depends on the trained model and available food classes.
* This dashboard is intended for educational and analytical purposes, not for medical diagnosis.
* The nutrition information should be interpreted as an estimation, not as a substitute for professional dietary advice.


