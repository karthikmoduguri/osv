import os
import uuid
import base64
import cv2
import numpy as np

from db.mongo import users
from model.user_model import create_user_doc
from services.static_embedding import get_embedding, advanced_preprocess,preprocess
from services.dynamic_features import extract_physics_features_from_strokes
from services.threshold import compute_threshold

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "..", "uploads")
UPLOAD_DIR = os.path.abspath(UPLOAD_DIR)

os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_base64_image(base64_string):
    img_data = base64_string.split(",")[1]
    img_bytes = base64.b64decode(img_data)

    filename = f"{uuid.uuid4()}.png"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(img_bytes)

    return file_path


def to_python(obj):
    if isinstance(obj, dict):
        return {k: to_python(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_python(i) for i in obj]
    elif hasattr(obj, "item"):
        return obj.item()
    else:
        return obj


def register_signature(data):
    user_id = str(uuid.uuid4())[:8]
    user_doc = create_user_doc(user_id)

    # 🔥 ADD THIS FIELD
    user_doc["user_images"] = []

    for sig in data["signatures"]:

        base64_image = sig.get("image")
        strokes = sig.get("strokes")

        if not base64_image or not strokes:
            return {"error": "Invalid signature payload"}, 400

        img_path = save_base64_image(base64_image)

        # ==========================
        # STATIC EMBEDDING
        # ==========================
        emb = get_embedding(img_path)

        # ==========================
        # DYNAMIC FEATURES
        # ==========================
        dyn = extract_physics_features_from_strokes(strokes)

        # ==========================
        # 🔥 SHAPE IMAGE (IMPORTANT)
        # ==========================
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

        processed = preprocess(img)[0] * 255
        processed = processed.astype("uint8")
        processed = cv2.cvtColor(processed, cv2.COLOR_RGB2GRAY)

        user_doc["user_images"].append(processed.tolist())

        # ==========================
        # STORE
        # ==========================
        user_doc["static_embeddings"].append(emb)
        user_doc["dynamic_features"].append(dyn)

    # ==========================
    # THRESHOLD
    # ==========================
    user_doc["threshold"] = compute_threshold(
        user_doc["static_embeddings"],
        user_doc["dynamic_features"]
    )

    clean_doc = to_python(user_doc)
    users.insert_one(clean_doc)

    return {
        "message": "Signature registered successfully",
        "user_id": user_id,
        "samples": len(user_doc["static_embeddings"])
    }, 200