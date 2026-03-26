import os
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "model", "rf_model.pkl")

rf_model = joblib.load(MODEL_PATH)


def predict_signature(features):
    prob = rf_model.predict_proba([features])[0][1]
    prediction = "Verified" if prob >= 0.5 else "Forgery"

    return {
        "prediction": prediction,
        "confidence": round(prob, 3)
    }
