import os, joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_squared_error
from core.feature_engineering import engineer_features, NUMERIC_FEATURES, CATEGORICAL_FEATURES, ALL_FEATURES

MODEL_DIR   = "models"
PRICING_PATH  = os.path.join(MODEL_DIR, "pricing_model.pkl")
OCCUPANCY_PATH = os.path.join(MODEL_DIR, "occupancy_model.pkl")
DATA_PATH   = "data/hotel_bookings.csv"

def _preprocessor():
    return ColumnTransformer([
        ('num', Pipeline([('imp', SimpleImputer(strategy='median')),
                          ('sc',  StandardScaler())]), NUMERIC_FEATURES),
        ('cat', Pipeline([('imp', SimpleImputer(strategy='most_frequent')),
                          ('enc', OneHotEncoder(handle_unknown='ignore', sparse_output=False))]),
                CATEGORICAL_FEATURES)
    ])

def train_models():
    print("Training models …")
    df = pd.read_csv(DATA_PATH)
    df = engineer_features(df)
    X  = df[ALL_FEATURES]
    os.makedirs(MODEL_DIR, exist_ok=True)

    # Pricing model
    pm = Pipeline([('pre', _preprocessor()),
                   ('reg', RandomForestRegressor(n_estimators=120, max_depth=12,
                                                  min_samples_split=4, random_state=42, n_jobs=-1))])
    pm.fit(X, df['adr'])
    joblib.dump(pm, PRICING_PATH)
    rmse = np.sqrt(mean_squared_error(df['adr'], pm.predict(X)))
    print(f"  Pricing  RMSE = {rmse:.2f}")

    # Occupancy model
    om = Pipeline([('pre', _preprocessor()),
                   ('reg', GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42))])
    om.fit(X, df['occupancy_rate'])
    joblib.dump(om, OCCUPANCY_PATH)
    rmse2 = np.sqrt(mean_squared_error(df['occupancy_rate'], om.predict(X)))
    print(f"  Occupancy RMSE = {rmse2:.4f}")
    return pm, om

def load_or_train_models():
    if os.path.exists(PRICING_PATH) and os.path.exists(OCCUPANCY_PATH):
        print("Loading saved models …")
        return joblib.load(PRICING_PATH), joblib.load(OCCUPANCY_PATH)
    return train_models()
