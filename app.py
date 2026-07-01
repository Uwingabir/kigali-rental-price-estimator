from flask import Flask, request, jsonify, render_template
import pandas as pd
import numpy as np
import joblib
import logging
import os
import sys

from flask_cors import CORS

app = Flask(__name__)

# Configure basic logging to STDOUT
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)
CORS(app)


# Load model and market stats
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "best_model.joblib")
STATS_PATH = os.path.join(BASE_DIR, "market_stats.joblib")

pipeline = None
market_stats = None

def load_models():
    """Load pre-trained models and statistics"""
    global pipeline, market_stats
    
    if os.path.exists(MODEL_PATH):
        try:
            logger.info(f"Loading trained model pipeline from {MODEL_PATH}...")
            pipeline = joblib.load(MODEL_PATH)
            logger.info("✓ Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}", exc_info=True)
            raise
    else:
        logger.error(f"Model file not found at {MODEL_PATH}")
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}")

    if os.path.exists(STATS_PATH):
        try:
            logger.info(f"Loading market statistics from {STATS_PATH}...")
            market_stats = joblib.load(STATS_PATH)
            logger.info("✓ Market statistics loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load market stats: {str(e)}", exc_info=True)
            raise
    else:
        logger.error(f"Market statistics not found at {STATS_PATH}")
        raise FileNotFoundError(f"Market statistics not found at {STATS_PATH}")

# Load models on startup
try:
    load_models()
    logger.info("✓ All models loaded successfully! App is ready.")
except Exception as e:
    logger.error(f"FATAL: Could not load models. App startup failed: {str(e)}")
    sys.exit(1)

@app.route('/')
def home():
    # Pass metadata categories to frontend dropdowns
    locations = []
    property_types = []
    
    if market_stats:
        # Sort locations alphabetically for dropdown accessibility
        locations = sorted([item['location'] for item in market_stats.get('location_stats', [])])
        property_types = sorted([item['property_type'] for item in market_stats.get('property_stats', [])])
    
    # Fallbacks in case stats are not loaded
    if not locations:
        locations = ["Kacyiru", "Kibagabaga", "Remera", "Rebero", "Gisozi", "Nyamirambo", "Gikondo", "Kagugu", "Nyarutarama", "Kimironko"]
    if not property_types:
        property_types = ["House", "Apartment", "Studio", "Single Room", "Other"]
        
    furnished_options = ["Unfurnished", "Semi-Furnished", "Furnished", "Unknown"]
    parking_options = ["Yes", "No", "Unknown"]
    security_options = ["Yes", "No", "Unknown"]
    road_options = ["Good", "Average", "Poor", "Unknown"]
    
    return render_template(
        'index.html',
        locations=locations,
        property_types=property_types,
        furnished_options=furnished_options,
        parking_options=parking_options,
        security_options=security_options,
        road_options=road_options
    )

@app.route('/api/stats', methods=['GET'])
def get_stats():
    if not market_stats:
        return jsonify({"error": "Market statistics not loaded"}), 500
    
    # Send stats to feed frontend dashboards and charts
    return jsonify({
        "total_listings": market_stats.get('total_listings', 0),
        "overall_avg_rent": market_stats.get('overall_avg_rent', 0),
        "location_stats": market_stats.get('location_stats', [])[:12], # top 12 locations by average price
        "property_stats": market_stats.get('property_stats', [])
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    if not pipeline:
        logger.error("Prediction model not loaded on server")
        return jsonify({"error": "Prediction model not loaded on server. Please try again in a moment."}), 500
        
    try:
        data = request.get_json()
        logger.info(f"Received prediction request: {data}")
        
        # Extract features and validate inputs
        bedrooms = int(data.get('bedrooms', 1))
        bathrooms = int(data.get('bathrooms', 1))
        amenities_count = int(data.get('amenities_count', 0))
        
        location = data.get('location')
        property_type = data.get('property_type')
        furnished_status = data.get('furnished_status', 'Unknown')
        parking = data.get('parking', 'Unknown')
        security = data.get('security', 'Unknown')
        road_access = data.get('road_access', 'Unknown')
        
        # Validate required fields
        if not location or not property_type:
            logger.warning(f"Missing required fields: location={location}, property_type={property_type}")
            return jsonify({"error": "Location and Property Type are required"}), 400
        
        # User input rent to check (optional)
        listed_rent = data.get('listed_rent')
        if listed_rent is not None:
            listed_rent = float(listed_rent)
            
        # Create input DataFrame (matching exact column order and names in training)
        input_data = pd.DataFrame([{
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'amenities_count': amenities_count,
            'location': location,
            'property_type': property_type,
            'furnished_status': furnished_status,
            'parking': parking,
            'security': security,
            'road_access': road_access
        }])
        
        logger.info(f"Input data prepared: {input_data.to_dict()}")
        
        # Predict using pipeline (point estimate)
        predicted_val = pipeline.predict(input_data)[0]
        logger.info(f"Prediction successful: {predicted_val}")

        # Post-process predictions: rent cannot be negative
        predicted_rent = max(0.0, float(predicted_val))

        # Try to compute a model-based prediction interval when possible
        # For RandomForestRegressor we can use per-tree predictions and take percentiles
        rent_min = None
        rent_max = None

        try:
            from sklearn.pipeline import Pipeline as _Pipeline

            final_estimator = pipeline
            X_trans = input_data

            # If the pipeline is a scikit-learn Pipeline, extract the final estimator
            if isinstance(pipeline, _Pipeline):
                final_estimator = pipeline.steps[-1][1]
                # transform inputs through the pipeline (all but last) if possible
                if len(pipeline.steps) > 1 and hasattr(pipeline[:-1], 'transform'):
                    X_trans = pipeline[:-1].transform(input_data)

            # If final estimator exposes individual trees (RandomForest), build quantile interval
            if hasattr(final_estimator, 'estimators_'):
                # Collect each tree's prediction for the input and compute percentiles
                tree_preds = np.vstack([est.predict(X_trans) for est in final_estimator.estimators_])
                lower = float(np.percentile(tree_preds, 5))
                upper = float(np.percentile(tree_preds, 95))
                rent_min = round(max(0.0, lower))
                rent_max = round(max(0.0, upper))
        except Exception as e:
            logger.debug(f"Could not compute ensemble interval: {e}")

        # Fallback to a heuristic ±12% margin when model-based interval is not available
        if rent_min is None or rent_max is None:
            margin = 0.12
            rent_min = round(predicted_rent * (1 - margin))
            rent_max = round(predicted_rent * (1 + margin))

        # If available, widen interval by the model's MAE to avoid incorrectly strict assessments
        try:
            mae = None
            if market_stats:
                # look for stored metrics produced by training
                mae = market_stats.get('best_model_metrics', {}).get('MAE') or market_stats.get('mae')
            if mae:
                mae = float(mae)
                rent_min = round(min(rent_min, predicted_rent - mae))
                rent_max = round(max(rent_max, predicted_rent + mae))
        except Exception:
            pass

        predicted_rent = round(predicted_rent)

        # Assess listed price if provided; otherwise mark as fair market baseline
        if listed_rent is not None:
            price_diff_percent = round(((listed_rent - predicted_rent) / predicted_rent) * 100, 1) if predicted_rent > 0 else 0
            if listed_rent < rent_min:
                price_status = "Underpriced"
            elif listed_rent > rent_max:
                price_status = "Overpriced"
            else:
                price_status = "Fair Market"
        else:
            # No comparison price entered; the estimate itself is the fair market value
            price_status = "Fair Market"
            price_diff_percent = 0.0
                
        response_payload = {
            "status": "success",
            "predicted_rent": predicted_rent,
            "rent_min": rent_min,
            "rent_max": rent_max,
            "listed_rent": listed_rent,
            "price_status": price_status,
            "price_diff_percent": price_diff_percent
        }

        # Include model MAE if available to help users understand typical error magnitude
        try:
            if market_stats:
                mae_val = market_stats.get('best_model_metrics', {}).get('MAE') or market_stats.get('mae')
                if mae_val is not None:
                    response_payload['model_mae'] = round(float(mae_val))
        except Exception:
            pass

        return jsonify(response_payload)
        
    except ValueError as e:
        logger.error(f"Value error during prediction: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Invalid input values: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"Error during prediction: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Prediction error: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Run locally on port 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
