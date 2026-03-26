import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import os

# load global RF model (trained on GPDS / SVC)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "model", "rf_model.pkl")
)

rf_model = joblib.load(MODEL_PATH)


def compute_dynamic_score(new_dynamic, stored_dynamics, beta=0.6):

    # ===============================
    # 1️⃣ USER-SPECIFIC SIMILARITY
    # ===============================
    sims = []

    for d in stored_dynamics:
        sim = cosine_similarity(
            [new_dynamic], [d]
        )[0][0]
        sims.append(sim)

    S_dynamic_user = np.mean(sims)

    # ===============================
    # 2️⃣ RF PROBABILITY
    # ===============================
    P_RF = rf_model.predict_proba(
        [new_dynamic]
    )[0][1]   # genuine class probability

    # ===============================
    # 3️⃣ HYBRID DYNAMIC SCORE
    # ===============================
    Dynamic_Score = (
        beta * S_dynamic_user
        +
        (1 - beta) * P_RF
    )

    return float(Dynamic_Score)