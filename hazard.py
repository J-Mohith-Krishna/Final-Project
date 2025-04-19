import numpy as np
import joblib

model = joblib.load("hazard_model.pkl")  

def predict_hazard_score(latitude, longitude):
    """
    Predict hazard score based on latitude and longitude.
    """
    features = np.array([[latitude, longitude]])  

    hazard_score = model.predict(features)
    return float(hazard_score)
