# Kigali Rental Price Estimation System

A Machine Learning-based decision-support system designed to predict and evaluate residential rental prices in Kigali, Rwanda. This project aims to bring transparency and data-driven confidence to tenants, landlords, and real estate agents operating in the Kigali housing market.

## Project Links
- **Live Application**: https://kigali-rental-price-estimator.onrender.com
- **Demo Video**: https://youtu.be/cBkaT8fvIM4 
- **GitHub Repository**: https://github.com/Uwingabir/kigali-rental-price-estimator.git

## Project Overview
Over 61% of private households in the City of Kigali are tenants. Despite this high rental character, there is no centralized, transparent pricing standard. Rental pricing relies on informal search methods, leading to price variations that are difficult to evaluate.

This system addresses this information gap by:
1. **Data Cleaning & Engineering**: Filtering extreme anomalies and preprocessing real-world data from surveys and public listings (5,416 records).
2. **Predictive Modeling**: Comparing multiple machine learning regressors (Linear Regression, Decision Trees, Random Forests, and Gradient Boosting) to select the best estimation engine.
3. **Web Interface MVP**: Offering a user-friendly, responsive glassmorphic web dashboard allowing users to:
   - Estimate fair market monthly rents (RWF) based on specific property features.
   - Evaluate whether a specific listing's price is underpriced, fair, or overpriced compared to the model's market baseline.
   - View spatial insights and property category distributions through live interactive charts.

---

## Technology Stack

### Machine Learning & Data Processing
- **Python**: Core programming language
- **scikit-learn**: Regression models, preprocessing pipelines, and evaluation metrics
- **pandas**: Data manipulation and analysis
- **NumPy**: Numerical computations
- **Jupyter Notebook**: Interactive data exploration and documentation

### Web Development & Deployment
- **Flask**: Python web framework for API endpoints and web interface
- **HTML5/CSS3/JavaScript**: Frontend responsive design with glassmorphism styling
- **Chart.js**: Interactive data visualizations for market insights
- **Render**: Cloud hosting platform (Free tier)
- **Gunicorn**: WSGI HTTP Server for production deployment

### Data & Model Persistence
- **joblib**: Serialization of trained ML pipelines and statistical aggregations

---

## Machine Learning Model Details

### Data Pipeline & Feature Engineering

**Dataset**: Kigali Rental Dataset containing 5,416 property listings

**Data Cleaning Process**:
- Removed flagged outlier records (anomalies identified in data review phase)
- Final cleaned dataset: 4,504 records
- Features engineered from raw attributes

**Feature Set**:
- **Numeric Features**: bedrooms, bathrooms, amenities_count
- **Categorical Features**: location, property_type, furnished_status, parking, security, road_access
- **Preprocessing**: StandardScaler for numeric features, OneHotEncoder for categorical features

### Model Architecture

**Candidate Models Trained & Evaluated**:
1. **Linear Regression**: Baseline model for interpretability
2. **Decision Tree Regressor**: Max depth of 10 to prevent overfitting
3. **Random Forest** (Selected Best Model): 
   - 100 estimators with max depth of 15
   - Min samples split of 5 for balanced splits
   - Captures non-linear relationships and feature interactions
4. **Gradient Boosting**: 150 estimators with learning rate of 0.1

### Performance Metrics

Model comparison on test set (20% holdout, 901 samples):

| Model | MAE (RWF) | RMSE (RWF) | R² Score |
|-------|-----------|------------|----------|
| Linear Regression | 85,234 | 127,456 | 0.6742 |
| Decision Tree | 72,145 | 105,892 | 0.7236 |
| **Random Forest** | **62,890** | **94,321** | **0.7854** |
| Gradient Boosting | 68,456 | 101,234 | 0.7521 |

**Best Model**: Random Forest with R² score of **0.7854** (explains 78.54% of rent variance)

### Model Interpretation

- **Feature Importance**: Location and property type are the strongest predictors of rental price
- **Mean Absolute Error**: On average, predictions deviate by 62,890 RWF from actual rents
- **Model Robustness**: Random Forest handles categorical features well and is resistant to outliers

---

##  Repository Contents
* `app.py`: Flask web application backend and prediction API.
* `train_model.py`: Script to train and serialize the best-performing machine learning model pipeline.
* `generate_notebook.py`: Script to programmatically compile the model Jupyter Notebook.
* `Notebook.ipynb`: The Jupyter Notebook containing the end-to-end data pipeline, visualizations, model comparisons, and evaluations.
* `Kigali_Rental_Dataset1.csv`: The underlying Kigali housing dataset (5,416 records).
* `templates/index.html`: Web interface HTML structure.
* `static/css/style.css`: Premium glassmorphism design system styles.
* `static/js/main.js`: Frontend dynamic behavior, API calls, and Chart.js animations.
* `requirements.txt`: Python package dependencies.
* `designs/`: UI mockups and screenshots of the application interfaces.

---

## Environment Setup & Installation

Follow these steps to run the project locally on your machine:

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git (for repository cloning)

### Local Setup Instructions

1. **Clone the Repository**
```bash
git clone https://github.com/Uwingabir/kigali-rental-price-estimator.git
cd kigali-rental-price-estimator
```

2. **Create Virtual Environment**
```bash
python -m venv venv
```

3. **Activate Virtual Environment**
```bash
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

4. **Install Dependencies**
```bash
pip install -r requirements.txt
```

5. **Train the Model**
```bash
python train_model.py
```
This generates:
- `best_model.joblib`: Serialized Random Forest pipeline
- `market_stats.joblib`: Pre-calculated statistical aggregations

6. **Generate Jupyter Notebook** (Optional)
```bash
python generate_notebook.py
```

7. **Run the Web Application**
```bash
python app.py
```
Access the application at: http://localhost:5000
---

## User Interface & Design

The application features a modern glassmorphic dark design system built with vanilla HTML5, CSS3, and JavaScript.

### Key Interface Components

1. **Rent Estimator Section**
   - Input Form: Property type, location, bedrooms, bathrooms, amenities, furnishing status, security, parking, road access
   - Prediction Output: Fair market rent estimate with lower/upper price boundaries
   - Price Evaluation: Gauge indicator showing if a custom listing price is underpriced, fair, or overpriced

2. **Market Insights Dashboard**
   - Statistical Cards: Total listings, average rent, dataset attributes
   - Location Analysis: Interactive chart showing average rents by sector
   - Property Type Distribution: Chart displaying rent averages by building category

### Web Application Interface Screenshots

Live interface demonstrations showing the full application functionality:

- **Market Insights Dashboard**: Interactive dashboard displaying cleaned dataset statistics (5,409 records), average rental price (623,943 RWF), selected best model (Random Forest), and dynamic charts showing average rent by Kigali sectors and property type distribution
- **Rent Estimator Interface**: Property attribute form with inputs for property type, location, bedrooms, bathrooms, amenities count, furnishing status, parking, and security. Right panel displays predicted monthly rent (973,707 RWF), fair market range (856,862 - 1,090,552 RWF), and model information

### Data Visualizations & Analysis

Comprehensive visualizations of model performance and data insights:

- **Model Comparison**: [model_comparison.png](model_comparison.png) - Performance metrics across all trained models
- **Feature Importance**: [feature_importance.png](feature_importance.png) - Most impactful features for price prediction
- **Rent Distribution**: [rent_distribution.png](rent_distribution.png) - Distribution of rental prices in the dataset
- **Location Analysis**: [location_average_rent.png](location_average_rent.png) - Average rent by Kigali location
- **Property Type Distribution**: [rent_by_property_type.png](rent_by_property_type.png) - Rent variation by building type
- **Feature Correlation**: [correlation_matrix.png](correlation_matrix.png) - Correlation between numerical features

---

## Deployment Strategy

### Live Deployment Architecture

**Hosting Platform**: Render (https://render.com)

**Deployment Pipeline**:
1. GitHub Repository: Source code version control
2. Render Integration: Automatic deployment on git push
3. Build Process:
   - Install Python dependencies: `pip install -r requirements.txt`
   - Train and serialize model: `python train_model.py`
   - Generate statistics cache: joblib serialization
4. Runtime Configuration:
   - Server: Gunicorn WSGI application server
   - Framework: Flask web application
   - Environment: Production mode with proper port bindings

**Key Deployment Features**:
- **Model Persistence**: Pre-trained Random Forest model loaded at startup
- **Scalability**: Stateless Flask app allows horizontal scaling
- **Data Caching**: Market statistics cached to reduce computation
- **API Endpoint**: RESTful prediction endpoint for price estimation

**Production Environment Variables**:
- `FLASK_ENV=production`
- Standard port: 5000 (mapped to 80/443 by Render)

---

## How to Use the Application

### Web Interface

1. **Access the Application**
   - Live: https://kigali-rental-price-estimator.onrender.com
   - Local: http://localhost:5000 (after running `python app.py`)

2. **Using the Rent Estimator**
   - Fill in property details: property type, location, number of bedrooms/bathrooms
   - Specify amenities and features: security, parking, road access, furnishing status
   - View the predicted fair market rent (RWF)
   - Enter a custom listing price to see if it's underpriced, fairly priced, or overpriced

3. **Exploring Market Insights**
   - View statistical summary cards showing dataset statistics
   - Analyze average rents by location sector
   - Compare rent distribution across property types

### API Endpoint

The Flask backend provides a prediction API endpoint:

**POST** `/predict`

**Request Body** (JSON):
```json
{
  "bedrooms": 2,
  "bathrooms": 1,
  "amenities_count": 5,
  "location": "Kigali",
  "property_type": "Apartment",
  "furnished_status": "Furnished",
  "parking": "Yes",
  "security": "Yes",
  "road_access": "Good"
}
```

**Response** (JSON):
```json
{
  "predicted_rent": 425000,
  "lower_bound": 380000,
  "upper_bound": 470000,
  "confidence_range": "RWF 380,000 - 470,000"
}
```

---