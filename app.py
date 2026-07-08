from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import pandas as pd
import numpy as np
import joblib
import logging
import os
import sys
import json
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Load .env if present (local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask_cors import CORS
import db

# Initialize database tables & listings import
db.init_db()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "kigalirent-super-secret-key-123")

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
            logger.info("Model loaded successfully.")
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
            logger.info("Market statistics loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load market stats: {str(e)}", exc_info=True)
            raise
    else:
        logger.error(f"Market statistics not found at {STATS_PATH}")
        raise FileNotFoundError(f"Market statistics not found at {STATS_PATH}")

# Load models on startup
try:
    load_models()
    logger.info("All models loaded successfully! App is ready.")
except Exception as e:
    logger.error(f"FATAL: Could not load models. App startup failed: {str(e)}")
    sys.exit(1)

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

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
    stats = db.get_listings_stats()
    return jsonify({
        "total_listings": stats.get('total_listings', 0),
        "overall_avg_rent": stats.get('overall_avg_rent', 0),
        "location_stats": stats.get('location_stats', [])[:12], # top 12 locations
        "property_stats": stats.get('property_stats', [])
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

# ─── Seeding Admin & Demo Accounts ─────────────────────────────────────────────
def seed_admin():
    """Seed default admin and demo users if missing in DB."""
    # Admin
    if not db.find_user_by_phone('+250788000000'):
        db.add_user("u_admin", "+250788000000", "System Admin", "admin@kigalirent.com", generate_password_hash("admin123"), "admin", "active")
        logger.info("Default Admin account seeded (+250788000000 / admin123).")

    # Demo Seeker/Customer
    if not db.find_user_by_phone('+250788111111'):
        db.add_user("u_seeker_demo", "+250788111111", "Caline Seeker", "seeker.demo@kigalirent.com", generate_password_hash("seeker123"), "customer", "active")
        logger.info("Demo Seeker account seeded (+250788111111 / seeker123).")

    # Demo Agent/Commissioner
    if not db.find_user_by_phone('+250788222222'):
        db.add_user("u_agent_demo", "+250788222222", "Norah Agent", "agent.demo@kigalirent.com", generate_password_hash("agent123"), "commissioner", "active")
        logger.info("Demo Agent account seeded (+250788222222 / agent123).")

seed_admin()

# ─── Twilio WhatsApp Helper ────────────────────────────────────────────────────
def send_whatsapp_notification(inquiry: dict) -> tuple[bool, str]:
    """
    Send a formatted WhatsApp message to the commissioner via Twilio.
    Returns (success: bool, message: str).
    """
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    auth_token  = os.environ.get("TWILIO_AUTH_TOKEN", "")
    from_number = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    to_number   = os.environ.get("COMMISSIONER_WHATSAPP_NUMBER", "")

    if not account_sid or not auth_token or not to_number:
        logger.info("Twilio credentials not set — skipping WhatsApp notification.")
        return False, "WhatsApp not configured"

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)

        prop = inquiry.get("property", {})
        msg_body = (
            f"*New Rental Inquiry — KigaliRent*\n\n"
            f"Customer: {inquiry.get('name', 'N/A')}\n"
            f"Phone: {inquiry.get('phone', 'N/A')}\n"
            f"Email: {inquiry.get('email', 'N/A')}\n\n"
            f"Property Interest:\n"
            f"  - Type: {prop.get('property_type', 'N/A')}\n"
            f"  - Location: {prop.get('location', 'N/A')}\n"
            f"  - Bedrooms: {prop.get('bedrooms', 'N/A')} | Bathrooms: {prop.get('bathrooms', 'N/A')}\n"
            f"  - Estimated Rent: {prop.get('rent_min', 'N/A'):,} - {prop.get('rent_max', 'N/A'):,} RWF/month\n\n"
            f"Move-in Date: {inquiry.get('move_in_date', 'N/A')}\n"
            f"Max Budget: {inquiry.get('budget', 'N/A')} RWF\n\n"
            f"Notes: {inquiry.get('notes', 'None')}\n\n"
            f"Sent via KigaliRent Estimator"
        )

        client.messages.create(
            body=msg_body,
            from_=from_number,
            to=to_number
        )
        logger.info("WhatsApp notification sent to commissioner.")
        return True, "WhatsApp sent"
    except Exception as e:
        logger.error(f"Twilio WhatsApp error: {e}")
        return False, str(e)


# ─── Authentication API Endpoints ─────────────────────────────────────────────
@app.route('/login')
def login_page():
    """Render the Login/Signup page."""
    return render_template('auth.html')


@app.route('/api/register', methods=['POST'])
def register():
    """Register a new customer or commissioner."""
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        role = data.get('role', 'customer').strip()

        if not phone or not name or not password:
            return jsonify({"error": "Missing required registration details"}), 400

        if role not in ['customer', 'commissioner']:
            return jsonify({"error": "Invalid role specified"}), 400

        if db.find_user_by_phone(phone):
            return jsonify({"error": "Phone number is already registered"}), 400

        # Commissioners are created as pending_approval; Customers are active
        status = "pending_approval" if role == 'commissioner' else "active"
        user_id = "u_" + datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")

        db.add_user(user_id, phone, name, email, generate_password_hash(password), role, status)

        msg = "Registration successful."
        if role == 'commissioner':
            msg += " Your agent account is pending approval by an administrator."

        return jsonify({"status": "success", "message": msg, "role": role})

    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate user and initialize Flask session."""
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        password = data.get('password', '')

        if not phone or not password:
            return jsonify({"error": "Missing login credentials"}), 400

        user = db.find_user_by_phone(phone)

        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({"error": "Invalid phone number or password"}), 401

        # Restrict pending approval accounts
        if user.get('status') == 'pending_approval':
            return jsonify({"error": "Your agent account is pending approval by an administrator. Please try again later."}), 403
        
        if user.get('status') == 'suspended':
            return jsonify({"error": "Your account has been suspended by an administrator."}), 403

        # Set session
        session.clear()
        session['user_id'] = user['id']
        session['phone'] = user['phone']
        session['name'] = user['name']
        session['role'] = user['role']

        return jsonify({
            "status": "success",
            "message": "Welcome back!",
            "user": {
                "id": user['id'],
                "phone": user['phone'],
                "name": user['name'],
                "role": user['role']
            }
        })

    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    """Clear Flask session."""
    session.clear()
    return jsonify({"status": "success", "message": "Logged out successfully"})


@app.route('/api/auth-state', methods=['GET'])
def auth_state():
    """Check current user session."""
    if 'user_id' in session:
        return jsonify({
            "logged_in": True,
            "user": {
                "id": session['user_id'],
                "phone": session['phone'],
                "name": session['name'],
                "role": session['role']
            }
        })
    return jsonify({"logged_in": False})


# ─── Contact Commissioner Route ───────────────────────────────────────────────
@app.route('/api/contact', methods=['POST'])
def contact_commissioner():
    """Receive a tenant inquiry, persist it, and notify the commissioner."""
    if 'user_id' not in session or session.get('role') != 'customer':
        return jsonify({"error": "Please sign in as a Customer to contact a commissioner."}), 401

    try:
        data = request.get_json()

        # Validate required fields
        required = ['name', 'phone', 'email']
        missing = [f for f in required if not data.get(f, '').strip()]
        if missing:
            return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

        # Build inquiry record
        inquiry = {
            "id": datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f"),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "customer_id": session['user_id'],
            "customer_phone": session['phone'],
            "name":         data.get('name', '').strip(),
            "phone":        data.get('phone', '').strip(),
            "email":        data.get('email', '').strip(),
            "move_in_date": data.get('move_in_date', '').strip(),
            "budget":       data.get('budget', '').strip(),
            "notes":        data.get('notes', '').strip(),
            "property": {
                "property_type": data.get('property_type', 'Not specified'),
                "location":      data.get('location', 'Not specified'),
                "bedrooms":      data.get('bedrooms', 'N/A'),
                "bathrooms":     data.get('bathrooms', 'N/A'),
                "amenities_count": data.get('amenities_count', 'N/A'),
                "furnished_status": data.get('furnished_status', 'N/A'),
                "parking":       data.get('parking', 'N/A'),
                "security":      data.get('security', 'N/A'),
                "road_access":   data.get('road_access', 'N/A'),
                "predicted_rent": data.get('predicted_rent'),
                "rent_min":      data.get('rent_min'),
                "rent_max":      data.get('rent_max'),
            },
            "whatsapp_sent": False
        }

        # Persist to SQLite
        db.save_inquiry(inquiry)
        logger.info(f"Inquiry saved: {inquiry['id']} from customer {session['name']}")

        # Send WhatsApp
        wa_ok, wa_msg = send_whatsapp_notification(inquiry)
        if wa_ok:
            db.update_inquiry_whatsapp_sent(inquiry["id"], True)
            inquiry["whatsapp_sent"] = True

        return jsonify({
            "status": "success",
            "message": "Your inquiry has been submitted. A commissioner will contact you soon.",
            "whatsapp_sent": wa_ok,
            "whatsapp_note": wa_msg
        })

    except Exception as e:
        logger.error(f"Contact route error: {e}", exc_info=True)
        return jsonify({"error": f"Could not submit inquiry: {str(e)}"}), 500


# ─── Commissioner Dashboard Template Route ──────────────────────────────────
@app.route('/dashboard')
def dashboard():
    """Render the separate Commissioner Dashboard page if logged in."""
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('dashboard.html')


# ─── Dynamic Dashboard Data Endpoint ──────────────────────────────────────────
@app.route('/api/dashboard/data', methods=['GET'])
def get_dashboard_data():
    """Fetch analytics and tables relative to the logged-in user's role."""
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized access"}), 401

    role = session['role']
    user_id = session['user_id']

    inquiries = db.load_inquiries()
    users = db.load_users()

    if role == 'customer':
        # Customers only see their own inquiries
        customer_inquiries = [i for i in inquiries if i.get('customer_id') == user_id]
        return jsonify({
            "role": "customer",
            "inquiries": customer_inquiries,
            "count": len(customer_inquiries)
        })

    elif role == 'commissioner':
        # Commissioners see all inquiries
        return jsonify({
            "role": "commissioner",
            "inquiries": inquiries,
            "count": len(inquiries)
        })

    elif role == 'admin':
        user_list = []
        for u in users:
            user_list.append({
                "id": u.get('id'),
                "phone": u.get('phone'),
                "name": u.get('name'),
                "email": u.get('email'),
                "role": u.get('role'),
                "status": u.get('status'),
                "created_at": u.get('created_at', '—')
            })

        total_customers = sum(1 for u in users if u.get('role') == 'customer')
        total_commissioners = sum(1 for u in users if u.get('role') == 'commissioner')

        return jsonify({
            "role": "admin",
            "stats": {
                "total_users": len(users),
                "total_customers": total_customers,
                "total_commissioners": total_commissioners,
                "total_inquiries": len(inquiries)
            },
            "users": user_list,
            "inquiries": inquiries
        })

    return jsonify({"error": "Invalid role session"}), 400


# ─── Admin Action Endpoint ───────────────────────────────────────────────────
@app.route('/api/admin/toggle-user', methods=['POST'])
def toggle_user_status():
    """Admin endpoint to activate, suspend, or approve users."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({"error": "Admin credentials required"}), 403

    try:
        data = request.get_json()
        target_id = data.get('user_id')
        new_status = data.get('status') # 'active' or 'suspended'

        if not target_id or new_status not in ['active', 'suspended']:
            return jsonify({"error": "Invalid status toggle parameters"}), 400

        user = db.find_user_by_id(target_id)
        if not user:
            return jsonify({"error": "Target user not found"}), 404
        if user.get('role') == 'admin':
            return jsonify({"error": "Cannot change status of an Admin account"}), 400

        db.update_user_status(target_id, new_status)
        return jsonify({
            "status": "success",
            "message": f"User status updated to {new_status} successfully."
        })

    except Exception as e:
        logger.error(f"Admin toggle user error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Run locally on port 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
