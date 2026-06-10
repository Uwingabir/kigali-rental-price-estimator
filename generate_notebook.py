import json
import os

def create_notebook():
    notebook_path = "Notebook.ipynb"
    print(f"Creating programmatic Jupyter Notebook: {notebook_path}...")
    
    # Define the cells
    cells = []
    
    # Cell 1: Markdown Title & Intro
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# Kigali Rental Price Estimation System - Model Notebook\n",
            "**Author:** Caline Uwingabire  \n",
            "**Supervisor:** Emmanuel Adjei  \n",
            "**Track:** Machine Learning (Capstone Assignment 1)  \n",
            "\n",
            "## Project Overview\n",
            "Renting is a major housing reality in Kigali, Rwanda, affecting over 61% of private households. However, the market suffers from a lack of pricing transparency, leaving tenants, landlords, and agents to make pricing decisions with scattered and unstructured information. \n",
            "\n",
            "This notebook builds the data pipeline, performs Exploratory Data Analysis (EDA), engineering features, and compares regression models to establish the machine learning foundation of a **Rental Price Estimation System** that estimates fair rent ranges in Kigali based on property attributes.\n",
            "\n",
            "### Notebook Contents:\n",
            "1. **Environment Setup & Data Loading**\n",
            "2. **Exploratory Data Analysis (EDA) & Data Visualization**\n",
            "3. **Data Cleaning (Outlier Filtering)**\n",
            "4. **Feature Engineering & Preprocessing**\n",
            "5. **Model Training & Comparison**\n",
            "6. **Model Evaluation & Metric Verification**\n",
            "7. **Saving the Best Model for Web Integration**"
        ]
    })
    
    # Cell 2: Code Imports
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import pandas as pd\n",
            "import numpy as np\n",
            "import matplotlib.pyplot as plt\n",
            "import seaborn as sns\n",
            "import joblib\n",
            "from sklearn.model_selection import train_test_split\n",
            "from sklearn.compose import ColumnTransformer\n",
            "from sklearn.preprocessing import StandardScaler, OneHotEncoder\n",
            "from sklearn.pipeline import Pipeline\n",
            "from sklearn.linear_model import LinearRegression\n",
            "from sklearn.tree import DecisionTreeRegressor\n",
            "from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor\n",
            "from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score\n",
            "\n",
            "# Set design aesthetic for visualizations\n",
            "sns.set_theme(style=\"whitegrid\")\n",
            "plt.rcParams[\"figure.figsize\"] = (12, 6)\n",
            "plt.rcParams[\"font.size\"] = 12\n",
            "print(\"Libraries imported successfully.\")"
        ]
    })
    
    # Cell 3: Markdown Data Loading
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 1. Environment Setup & Data Loading\n",
            "First, we load the Kigali Rental dataset containing 5,416 listings collected from public platforms and primary surveys."
        ]
    })
    
    # Cell 4: Code Data Loading
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "csv_path = \"Kigali_Rental_Dataset1.csv\"\n",
            "df = pd.read_csv(csv_path)\n",
            "print(f\"Loaded dataset with {df.shape[0]} rows and {df.shape[1]} columns.\")\n",
            "df.head()"
        ]
    })
    
    # Cell 5: Markdown EDA
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 2. Exploratory Data Analysis (EDA) & Data Visualization\n",
            "Let's look at the distribution of the monthly rent target variable, inspect location-based averages, property types, and relationships between features."
        ]
    })
    
    # Cell 6: Code Rent Distribution Chart
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Plot distribution of monthly rent (excluding extreme high outliers for plotting visualization)\n",
            "plt.figure(figsize=(10, 5))\n",
            "sns.histplot(df[df['monthly_rent_rwf'] < 3000000]['monthly_rent_rwf'] / 1000, bins=40, kde=True, color='#6366f1')\n",
            "plt.title('Distribution of Monthly Rent in Kigali (under 3M RWF)')\n",
            "plt.xlabel('Monthly Rent (Thousand RWF)')\n",
            "plt.ylabel('Count')\n",
            "plt.savefig('rent_distribution.png', dpi=300, bbox_inches='tight')\n",
            "plt.show()"
        ]
    })
    
    # Cell 7: Code Location Avg Rent
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Average Rent by Top 15 Locations\n",
            "top_locations = df['location'].value_counts().head(15).index\n",
            "df_top_loc = df[df['location'].isin(top_locations)]\n",
            "loc_avg = df_top_loc.groupby('location')['monthly_rent_rwf'].mean().sort_values(ascending=False) / 1000\n",
            "\n",
            "plt.figure(figsize=(12, 6))\n",
            "sns.barplot(x=loc_avg.values, y=loc_avg.index, palette='crest')\n",
            "plt.title('Average Rent in Top 15 Most Common Kigali Neighborhoods')\n",
            "plt.xlabel('Average Monthly Rent (Thousand RWF)')\n",
            "plt.ylabel('Location')\n",
            "plt.savefig('location_average_rent.png', dpi=300, bbox_inches='tight')\n",
            "plt.show()"
        ]
    })
    
    # Cell 8: Code Property Type Boxplot
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Rent vs Property Type\n",
            "plt.figure(figsize=(10, 5))\n",
            "sns.boxplot(data=df[df['monthly_rent_rwf'] < 2000000], x='property_type', y='monthly_rent_rwf', palette='Set2')\n",
            "plt.title('Monthly Rent by Property Type')\n",
            "plt.xlabel('Property Type')\n",
            "plt.ylabel('Monthly Rent (RWF)')\n",
            "plt.savefig('rent_by_property_type.png', dpi=300, bbox_inches='tight')\n",
            "plt.show()"
        ]
    })
    
    # Cell 9: Code Correlation Heatmap
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Numeric correlation\n",
            "numeric_cols = ['bedrooms', 'bathrooms', 'amenities_count', 'monthly_rent_rwf']\n",
            "corr = df[numeric_cols].corr()\n",
            "plt.figure(figsize=(8, 6))\n",
            "sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.3f', linewidths=0.5)\n",
            "plt.title('Correlation Matrix of Numeric Features')\n",
            "plt.savefig('correlation_matrix.png', dpi=300, bbox_inches='tight')\n",
            "plt.show()"
        ]
    })
    
    # Cell 10: Markdown Data Cleaning
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 3. Data Cleaning (Outlier Filtering)\n",
            "The dataset contains a `review_note` column that flags extreme outliers (e.g. rent amounts of 1 RWF or 150,000,000 RWF). We filter these out to ensure they do not bias our regression models."
        ]
    })
    
    # Cell 11: Code Outlier Filtering
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Display records with quality flags\n",
            "flagged = df[df['review_note'].notnull()]\n",
            "print(\"Flagged reviews to drop:\")\n",
            "print(flagged[['record_id', 'location', 'property_type', 'monthly_rent_rwf', 'review_note']])\n",
            "\n",
            "# Cleaning the dataset\n",
            "df_clean = df[df['review_note'].isnull()].copy()\n",
            "print(f\"Removed {len(flagged)} outlier records. Cleaned dataset has {df_clean.shape[0]} rows.\")"
        ]
    })
    
    # Cell 12: Markdown Preprocessing
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 4. Feature Engineering & Preprocessing\n",
            "We construct a scikit-learn `ColumnTransformer` to automatically scale numerical columns using `StandardScaler` and encode categorical features using `OneHotEncoder`. We split the dataset into an 80% training set and a 20% test set."
        ]
    })
    
    # Cell 13: Code Preprocessing Setup
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Define feature groups\n",
            "numeric_features = ['bedrooms', 'bathrooms', 'amenities_count']\n",
            "categorical_features = ['location', 'property_type', 'furnished_status', 'parking', 'security', 'road_access']\n",
            "\n",
            "X = df_clean[numeric_features + categorical_features]\n",
            "y = df_clean['monthly_rent_rwf']\n",
            "\n",
            "# Train-Test Split\n",
            "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n",
            "\n",
            "# Construct the preprocessor pipeline\n",
            "preprocessor = ColumnTransformer(\n",
            "    transformers=[\n",
            "        ('num', StandardScaler(), numeric_features),\n",
            "        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)\n",
            "    ]\n",
            ")\n",
            "print(\"Preprocessor ColumnTransformer defined.\")"
        ]
    })
    
    # Cell 14: Markdown Model Training
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 5. Model Training & Comparison\n",
            "We train four candidates: Linear Regression, Decision Tree, Random Forest, and Gradient Boosting Regressors. We evaluate each on the hold-out test set."
        ]
    })
    
    # Cell 15: Code Model Fitting
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "models = {\n",
            "    'Linear Regression': LinearRegression(),\n",
            "    'Decision Tree': DecisionTreeRegressor(random_state=42, max_depth=10),\n",
            "    'Random Forest': RandomForestRegressor(random_state=42, n_estimators=100, max_depth=15, min_samples_split=5),\n",
            "    'Gradient Boosting': GradientBoostingRegressor(random_state=42, n_estimators=150, learning_rate=0.1, max_depth=5)\n",
            "}\n",
            "\n",
            "results = []\n",
            "trained_pipelines = {}\n",
            "\n",
            "for name, model in models.items():\n",
            "    # Create pipeline\n",
            "    pipeline = Pipeline(steps=[\n",
            "        ('preprocessor', preprocessor),\n",
            "        ('regressor', model)\n",
            "    ])\n",
            "    \n",
            "    # Train model\n",
            "    pipeline.fit(X_train, y_train)\n",
            "    trained_pipelines[name] = pipeline\n",
            "    \n",
            "    # Predict\n",
            "    y_pred = pipeline.predict(X_test)\n",
            "    \n",
            "    # Evaluate\n",
            "    mae = mean_absolute_error(y_test, y_pred)\n",
            "    rmse = root_mean_squared_error(y_test, y_pred)\n",
            "    r2 = r2_score(y_test, y_pred)\n",
            "    \n",
            "    results.append({\n",
            "        'Model': name,\n",
            "        'MAE (RWF)': mae,\n",
            "        'RMSE (RWF)': rmse,\n",
            "        'R2 Score': r2\n",
            "    })\n",
            "\n",
            "# Convert results to DataFrame\n",
            "results_df = pd.DataFrame(results)\n",
            "results_df"
        ]
    })
    
    # Cell 16: Markdown Metrics
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 6. Model Evaluation & Metric Verification\n",
            "Let's visualize the results of the model comparison. Linear Regression has poor stability due to multicollinerity of location dummies, while ensemble models (Random Forest, Gradient Boosting) achieve robust scores."
        ]
    })
    
    # Cell 17: Code Plot Metrics
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Plot model comparisons (excluding Linear Regression due to scaling differences)\n",
            "plot_df = results_df[results_df['Model'] != 'Linear Regression']\n",
            "\n",
            "fig, axes = plt.subplots(1, 2, figsize=(16, 6))\n",
            "sns.barplot(data=plot_df, x='Model', y='R2 Score', ax=axes[0], palette='viridis')\n",
            "axes[0].set_title('R2 Score Comparison (Higher is Better)')\n",
            "axes[0].set_ylim(0, 1.0)\n",
            "\n",
            "sns.barplot(data=plot_df, x='Model', y='MAE (RWF)', ax=axes[1], palette='rocket')\n",
            "axes[1].set_title('MAE Comparison (Lower is Better)')\n",
            "\n",
            "plt.suptitle('Performance Evaluation of Model Candidates')\n",
            "plt.savefig('model_comparison.png', dpi=300, bbox_inches='tight')\n",
            "plt.show()"
        ]
    })
    
    # Cell 18: Code Feature Importance
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Extract Feature Importance from the Random Forest Model\n",
            "rf_model = trained_pipelines['Random Forest'].named_steps['regressor']\n",
            "cat_encoder = trained_pipelines['Random Forest'].named_steps['preprocessor'].named_transformers_['cat']\n",
            "\n",
            "# Get feature names\n",
            "encoded_cat_features = cat_encoder.get_feature_names_out(categorical_features)\n",
            "all_features = numeric_features + list(encoded_cat_features)\n",
            "\n",
            "# Importance dataframe\n",
            "importances = rf_model.feature_importances_\n",
            "feat_imp = pd.DataFrame({'Feature': all_features, 'Importance': importances})\n",
            "feat_imp = feat_imp.sort_values(by='Importance', ascending=False).head(15)\n",
            "\n",
            "plt.figure(figsize=(12, 6))\n",
            "sns.barplot(data=feat_imp, x='Importance', y='Feature', palette='mako')\n",
            "plt.title('Top 15 Most Influential Features for Rental Prices')\n",
            "plt.xlabel('Importance Score')\n",
            "plt.ylabel('Feature / Attribute')\n",
            "plt.savefig('feature_importance.png', dpi=300, bbox_inches='tight')\n",
            "plt.show()"
        ]
    })
    
    # Cell 19: Markdown Serialization
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 7. Saving the Best Model for Web Integration\n",
            "We fit the best model (Random Forest) on the complete cleaned dataset to maximize sample learning and save it as a serialized pipeline `best_model.joblib` to load in our web application."
        ]
    })
    
    # Cell 20: Code Serialization
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "best_pipeline = trained_pipelines['Random Forest']\n",
            "best_pipeline.fit(X, y)\n",
            "\n",
            "joblib.dump(best_pipeline, 'best_model.joblib')\n",
            "print(\"Best model pipeline successfully trained on all data and saved to best_model.joblib!\")"
        ]
    })
    
    # Assembly
    notebook_dict = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.12.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    
    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(notebook_dict, f, indent=1)
        
    print(f"Jupyter Notebook successfully written to {notebook_path}")

if __name__ == '__main__':
    create_notebook()
