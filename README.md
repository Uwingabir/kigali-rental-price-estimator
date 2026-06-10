# Kigali Rental Price Estimation System

A Machine Learning-based decision-support system designed to predict and evaluate residential rental prices in Kigali, Rwanda. This project aims to bring transparency and data-driven confidence to tenants, landlords, and real estate agents operating in the Kigali housing market.

---

## 📌 Project Overview
Over 61% of private households in the City of Kigali are tenants. Despite this high rental character, there is no centralized, transparent pricing standard. Rental pricing relies on informal search methods, leading to price variations that are difficult to evaluate.

This system addresses this information gap by:
1. **Data Cleaning & Engineering**: Filtering extreme anomalies and preprocessing real-world data from surveys and public listings.
2. **Predictive Modeling**: Comparing multiple machine learning regressors (Linear Regression, Decision Trees, Random Forests, and Gradient Boosting) to select the best estimation engine.
3. **Web Interface MVP**: Offering a user-friendly, responsive glassmorphic web dashboard allowing users to:
   - Estimate fair market monthly rents (RWF) based on specific property features.
   - Evaluate whether a specific listing's price is underpriced, fair, or overpriced compared to the model's market baseline.
   - View spatial insights and property category distributions through live interactive charts.

---

## 🚀 Repository Contents
* `app.py`: Flask web application backend and prediction API.
* `train_model.py`: Script to train and serialize the best-performing machine learning model pipeline.
* `generate_notebook.py`: Script to programmatically compile the model Jupyter Notebook.
* `ModelNotebook.ipynb`: The Jupyter Notebook containing the end-to-end data pipeline, visualizations, model comparisons, and evaluations.
* `Kigali_Rental_Final_Combined_With_Dataset1.csv`: The underlying Kigali housing dataset (5,416 records).
* `templates/index.html`: Web interface HTML structure.
* `static/css/style.css`: Premium glassmorphism design system styles.
* `static/js/main.js`: Frontend dynamic behavior, API calls, and Chart.js animations.
* `requirements.txt`: Python package dependencies.
* `designs/`: UI mockups and screenshots of the application interfaces.

---

## 🛠️ Environment Setup & Installation

Follow these steps to run the project locally on your machine:

### 1. Prerequisites
Ensure you have Python 3.10+ installed on your system.

### 2. Clone the Repository & Install Dependencies
Open your terminal or command prompt and run:
```bash
# Clone the repository
git clone https://github.com/Uwingabir/kigali-rental-price-estimator.git
cd kigali-rental-price-estimator

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install the required libraries
pip install -r requirements.txt
```

### 3. Model Training & Serialization
To train the regression models and serialize the best pipeline, execute:
```bash
python train_model.py
```
This script cleans the dataset, prints model performance comparisons (MAE, RMSE, $R^2$), and generates:
- `best_model.joblib`: Serialized Random Forest pipeline.
- `market_stats.joblib`: Pre-calculated statistical aggregations for the web dashboard.

To generate the submission Jupyter Notebook:
```bash
python generate_notebook.py
```

### 4. Running the Web Application MVP
Launch the Flask development server:
```bash
python app.py
```
Open your browser and navigate to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🎨 User Interface & Design Process

The application is styled using a modern **glassmorphic dark design system** built from vanilla HTML5, CSS3, and JavaScript.

### Interface Sections:
1. **Rent Estimator**:
   - Left Panel: Form allowing users to specify property type, location, bedrooms, bathrooms, and details like security and parking. Includes a field to evaluate a custom listing price.
   - Right Panel: Outputs the predicted rent, lower/upper fair market boundaries, and a colored gauge that dynamically places a pointer to rate the listed rent (Underpriced, Fair, Overpriced).
2. **Market Insights**:
   - Active statistical cards showing cleaned dataset attributes.
   - Dynamic charts rendering spatial averages per sector (top Kigali locations) and building categories.

### Interface Screenshots:
* **Rent Estimator View**:
  ![Rent Estimator](designs/estimator_interface.png)
* **Market Insights View**:
  ![Market Insights](designs/insights_interface.png)

---

## 🌐 Deployment Plan

To host the application online for public access, the following infrastructure plan is recommended:

### Frontend & Backend API (Flask App):
* **Target Platform**: **Render** (Free Web Services tier) or **Railway**.
* **Configuration**:
  - Build Command: `pip install -r requirements.txt && python train_model.py && python generate_notebook.py`
  - Start Command: `gunicorn app:app` (on Render, add `gunicorn` to `requirements.txt`).
* **Environment Variables**: Set `FLASK_ENV=production` and standard port bindings.

---

## 📹 Video Demonstration Guide (5 - 10 Mins)

Below is an outline to follow when recording your initial product demonstration video:

| Time | Slide/Section | Script & Demonstration Checklist |
|---|---|---|
| **0:00 - 1:00** | Introduction & Problem | Introduce yourself, state the project goal (Kigali rental price estimation), and show the problem slide (housing demand, tenant percentage, and lack of pricing transparency). |
| **1:00 - 2:30** | Data & ML Pipeline | Show the `ModelNotebook.ipynb`. Briefly scroll through the data distribution histograms, correlation heatmaps, model comparisons (explaining why Random Forest was selected with $R^2 = 0.7808$), and outlier cleaning process. |
| **2:30 - 4:30** | Estimator Live Demo | Show the web app running at `127.0.0.1:5000`. Enter details for an apartment in Kacyiru, predict the range, and input an overpriced/underpriced rent value to show how the pointer on the gauge shifts. |
| **4:30 - 5:30** | Insights Dashboard | Navigate to the "Market Insights" tab. Point out the live stats and describe the interactive Chart.js visualizations (average rent by neighborhood and distribution by housing type). |
| **5:30 - 6:00** | Conclusion & Next Steps | Summarize achievements (flawless environment setup, robust model training, and highly interactive UI). Discuss upcoming steps, including remote cloud deployment. |
