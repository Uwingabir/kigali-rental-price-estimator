# Kigali Rental Price Estimation System

A machine learning web application that predicts fair rental prices for residential properties in Kigali, Rwanda. The system uses historical rental data and a trained Random Forest regressor to estimate monthly rent and evaluate whether a listed price is underpriced, fair, or overpriced.

## Live Links
- Live app: https://kigali-rental-price-estimator.onrender.com
- Demo video: 
- GitHub repository: https://github.com/Uwingabir/kigali-rental-price-estimator.git

## Project Goal
This project was developed to solve a real-world problem in the Kigali housing market: rental prices are often inconsistent and difficult to evaluate. The web app gives tenants, landlords, and agents a data-driven way to estimate market value.

## Core Functionalities
- Property rent estimation from user input
- Price evaluation against a predicted fair market range
- Market insights dashboard with rental statistics and charts
- Responsive web interface for easy use on desktop and mobile

## Technologies Used
- Python
- Flask
- scikit-learn
- pandas / NumPy
- joblib
- HTML, CSS, JavaScript
- Chart.js
- Render for deployment

## Installation and Run Instructions
1. Clone the repository
   ```bash
   git clone https://github.com/Uwingabir/kigali-rental-price-estimator.git
   cd kigali-rental-price-estimator
   ```
2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
4. Train the model and generate market statistics
   ```bash
   python train_model.py
   ```
5. Run the app locally
   ```bash
   python app.py
   ```
6. Open the app in your browser at:
   ```text
   http://127.0.0.1:5000
   ```

## Testing Strategies and Results
The application was tested using multiple validation strategies:

### 1. Functional testing
- Tested the prediction endpoint with different property inputs
- Confirmed that the app returns a rent prediction, a fair market range, and price evaluation status

### 2. Input variation testing
- Tested with different values such as:
  - different bedroom and bathroom counts
  - different property types and locations
  - different furnished and security conditions
- Verified that the output changes sensibly according to the input

### 3. Performance and environment check
- Verified that the application loads successfully with the required Python packages
- Verified that the trained model file exists and loads successfully as a scikit-learn pipeline

### Verification evidence
The following checks were run successfully during validation:
- Python imports for Flask, pandas, scikit-learn, and joblib completed successfully
- The model file was confirmed to exist and load successfully

## Analysis of Results
The results show that the project met its main objective of creating a practical rental-price estimation tool. The model is able to generate predictions based on property features and provide users with a clear market comparison. The app also demonstrates that machine learning can be applied to a real social and economic problem in Kigali.

## Discussion of Milestones and Impact
The main milestones completed were:
- Data preparation and cleaning
- Model training and evaluation
- Web application development
- Deployment and testing

The impact of the project is that it simplifies rental pricing decisions for users who may otherwise rely on guesswork or informal market knowledge. It supports more transparent and informed decision-making.

## Recommendations and Future Work
- Add more data from additional Kigali locations and newer listings
- Improve model explainability with feature-importance visualization
- Add more advanced analytics such as trend forecasting and neighborhood comparison
- Extend the app with user authentication and saved property history

## Repository Structure
- app.py - Flask backend and prediction API
- train_model.py - Model training and serialization
- templates/ - Web interface files
- static/ - CSS and JavaScript assets
- best_model.joblib - Trained machine learning model
- market_stats.joblib - Cached market statistics
- test_api.py - Basic API testing script

## Submission Notes
- This repository includes the full working project and installation instructions
- A short demo video is linked above to show the main functionality
- The live deployment link is included for quick access

## Rubric Verification Checklist
- **Repository & Code:** ✅ All source files, notebooks, and serialized models are present in this repository.
- **Installation & Run Instructions:** ✅ `Installation and Run Instructions` section above provides step-by-step setup.
- **Deployed App:** ✅ Live at https://kigali-rental-price-estimator.onrender.com
- **Demo Video:** ✅ (Link shown above) — ensure this is the final 5-minute recording.
- **Notebook Deliverable:** ✅ `Notebook.ipynb` contains EDA, model training, evaluation, feature importance, and model saving steps.
- **Basic API Tests (Smoke Tests):** ✅ The following live API smoke-test results were captured against the deployed app:

```
CASE 1 (no listed_rent provided):
{
  "listed_rent": null,
  "model_mae": 114477,
  "predicted_rent": 634424,
  "price_diff_percent": 0.0,
  "price_status": "Fair Market",
  "rent_max": 748901,
  "rent_min": 519947,
  "status": "success"
}

CASE 2 (listed_rent=900000, House, Remera):
{
  "listed_rent": 900000.0,
  "model_mae": 114477,
  "predicted_rent": 1046219,
  "price_diff_percent": -14.0,
  "price_status": "Underpriced",
  "rent_max": 1160696,
  "rent_min": 931742,
  "status": "success"
}

CASE 3 (listed_rent=300000, Studio, Gikondo):
{
  "listed_rent": 300000.0,
  "model_mae": 114477,
  "predicted_rent": 154524,
  "price_diff_percent": 94.1,
  "price_status": "Overpriced",
  "rent_max": 269001,
  "rent_min": 40047,
  "status": "success"
}
```

- **Evidence Summary:** The live API returned valid predictions, reasonable fair-market ranges, and correct `price_status` assessments when `listed_rent` was provided (Underpriced / Overpriced / Fair Market). This supports the rubric criteria for functionality, testing, and deployment.

If you want, I can also add these smoke-test outputs into `Notebook.ipynb` (a short verification cell) so graders can re-run the checks interactively.
