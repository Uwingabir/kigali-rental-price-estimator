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

def train_models_if_needed():
    """Train models if they don't exist"""
    global pipeline, market_stats
    
    if not os.path.exists(MODEL_PATH) or not os.path.exists(STATS_PATH):
        logger.info("Model files not found. Training models...")
        try:
            from train_model import train_and_evaluate
            train_and_evaluate()
            logger.info("Model training completed successfully.")
        except Exception as e:
            logger.error(f"Failed to train models: {str(e)}")
            raise

def load_models():
    """Load trained models and statistics"""
    global pipeline, market_stats
    
    if os.path.exists(MODEL_PATH):
        try:
            logger.info(f"Loading trained model pipeline from {MODEL_PATH}...")
            pipeline = joblib.load(MODEL_PATH)
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
    else:
        logger.warning(f"Model not found at {MODEL_PATH}")

    if os.path.exists(STATS_PATH):
        try:
            logger.info(f"Loading market statistics from {STATS_PATH}...")
            market_stats = joblib.load(STATS_PATH)
            logger.info("Market statistics loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load market stats: {str(e)}")
    else:
        logger.warning(f"Market statistics not found at {STATS_PATH}")

# Initialize models on startup
train_models_if_needed()
load_models()

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
        
        # Predict using pipeline
        predicted_val = pipeline.predict(input_data)[0]
        logger.info(f"Prediction successful: {predicted_val}")
        
        # Post-process predictions: rent cannot be negative
        predicted_rent = max(0.0, float(predicted_val))
        
        # Calculate estimate range: e.g., standard confidence margin of ±12%
        margin = 0.12
        rent_min = round(predicted_rent * (1 - margin))
        rent_max = round(predicted_rent * (1 + margin))
        predicted_rent = round(predicted_rent)
        
        # Assess listed price if provided
        price_status = "Not Provided"
        price_diff_percent = 0.0
        
        if listed_rent is not None:
            price_diff_percent = round(((listed_rent - predicted_rent) / predicted_rent) * 100, 1) if predicted_rent > 0 else 0
            if listed_rent < rent_min:
                price_status = "Low"
            elif listed_rent > rent_max:
                price_status = "High"
            else:
                price_status = "Fair"
                
        return jsonify({
            "status": "success",
            "predicted_rent": predicted_rent,
            "rent_min": rent_min,
            "rent_max": rent_max,
            "listed_rent": listed_rent,
            "price_status": price_status,
            "price_diff_percent": price_diff_percent
        })
        
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
