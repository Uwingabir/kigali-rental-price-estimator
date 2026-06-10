import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

def train_and_evaluate():
    # 1. Load the dataset
    csv_path = "Kigali_Rental_Dataset1.csv"
    print(f"Loading dataset from: {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # 2. Data Cleaning
    # Remove records flagged in the review_note (outliers)
    initial_shape = df.shape
    df_clean = df[df['review_note'].isnull()].copy()
    cleaned_shape = df_clean.shape
    print(f"Cleaned dataset: Removed {initial_shape[0] - cleaned_shape[0]} flagged outlier rows. Shape changed from {initial_shape} to {cleaned_shape}.")
    
    # 3. Define features and target
    target_col = 'monthly_rent_rwf'
    numeric_features = ['bedrooms', 'bathrooms', 'amenities_count']
    categorical_features = ['location', 'property_type', 'furnished_status', 'parking', 'security', 'road_access']
    
    X = df_clean[numeric_features + categorical_features]
    y = df_clean[target_col]
    
    # 4. Train-Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Split data into train ({X_train.shape[0]} samples) and test ({X_test.shape[0]} samples).")
    
    # 5. Define preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ])
    
    # 6. Define candidate regression models
    models = {
        'Linear Regression': LinearRegression(),
        'Decision Tree': DecisionTreeRegressor(random_state=42, max_depth=10),
        'Random Forest': RandomForestRegressor(random_state=42, n_estimators=100, max_depth=15, min_samples_split=5),
        'Gradient Boosting': GradientBoostingRegressor(random_state=42, n_estimators=150, learning_rate=0.1, max_depth=5)
    }
    
    results = {}
    best_r2 = -float('inf')
    best_model_name = None
    best_pipeline = None
    
    print("\nTraining and evaluating models...")
    for name, model in models.items():
        # Create pipeline
        pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', model)
        ])
        
        # Train model
        pipeline.fit(X_train, y_train)
        
        # Predict
        y_pred = pipeline.predict(X_test)
        
        # Calculate metrics
        mae = mean_absolute_error(y_test, y_pred)
        rmse = root_mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        results[name] = {'MAE': mae, 'RMSE': rmse, 'R2': r2}
        print(f"{name:20} -> MAE: {mae:12.2f} RWF | RMSE: {rmse:12.2f} RWF | R2: {r2:.4f}")
        
        # Track best model based on R2 score
        if r2 > best_r2:
            best_r2 = r2
            best_model_name = name
            best_pipeline = pipeline
            
    print(f"\nBest Model: {best_model_name} with R2 Score: {best_r2:.4f}")
    
    # 7. Retrain the best model on the entire cleaned dataset for deployment
    print(f"Retraining the best model ({best_model_name}) on the complete cleaned dataset...")
    best_pipeline.fit(X, y)
    
    # 8. Save the best pipeline (contains both preprocessor and trained regressor)
    model_save_path = "best_model.joblib"
    joblib.dump(best_pipeline, model_save_path)
    print(f"Saved best model pipeline to: {model_save_path}")
    
    # Save statistics for Flask API to use (average rents by location, property type)
    print("Generating and saving location and property type stats...")
    location_stats = df_clean.groupby('location')[target_col].agg(['mean', 'count']).reset_index()
    location_stats.columns = ['location', 'avg_rent', 'listing_count']
    location_stats = location_stats.sort_values(by='avg_rent', ascending=False)
    
    property_stats = df_clean.groupby('property_type')[target_col].agg(['mean', 'count']).reset_index()
    property_stats.columns = ['property_type', 'avg_rent', 'listing_count']
    
    stats_data = {
        'location_stats': location_stats.to_dict(orient='records'),
        'property_stats': property_stats.to_dict(orient='records'),
        'total_listings': len(df_clean),
        'overall_avg_rent': float(df_clean[target_col].mean())
    }
    
    joblib.dump(stats_data, 'market_stats.joblib')
    print("Saved market stats to: market_stats.joblib")
    
if __name__ == '__main__':
    train_and_evaluate()
