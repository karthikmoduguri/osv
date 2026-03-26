import base64
import numpy as np
import uuid
import os
import cv2

from db.mongo import users
from services.static_matcher import compute_static_score
from services.dynamic_matcher import compute_dynamic_score
from services.static_embedding import get_embedding, advanced_preprocess
from services.dynamic_features import extract_physics_features_from_strokes


def save_temp_image(base64_string):

    if "," in base64_string:
        base64_string = base64_string.split(",")[1]

    img_bytes = base64.b64decode(base64_string)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "uploads")
    UPLOAD_FOLDER = os.path.abspath(UPLOAD_FOLDER)

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    filename = f"verify_{uuid.uuid4()}.png"
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    with open(file_path, "wb") as f:
        f.write(img_bytes)

    return file_path


def verify_signature(data):

    user_id = data.get("user_id")
    signature = data.get("signature", {})

    image_b64 = signature.get("image")
    strokes = signature.get("strokes")

    if not user_id or not image_b64 or not strokes:
        return {"error": "Missing required fields"}, 400

    user = users.find_one({"user_id": user_id})
    if not user:
        return {"error": "User not found"}, 404

    try:

        img_path = save_temp_image(image_b64)

        # ==========================
        # STATIC EMBEDDING
        # ==========================
        new_embedding = get_embedding(img_path)

        # ==========================
        # DYNAMIC FEATURES
        # ==========================
        new_dynamic = extract_physics_features_from_strokes(strokes)

        new_embedding = np.array(new_embedding).astype(float).tolist()
        new_dynamic = np.array(new_dynamic).astype(float).tolist()

        # ==========================
        # 🔥 PREPROCESS IMAGE SAME WAY
        # ==========================
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        new_img = advanced_preprocess(img)[0] * 255
        new_img = new_img.astype("uint8")
        new_img = cv2.cvtColor(new_img, cv2.COLOR_RGB2GRAY)

        # ==========================
        # LOAD STORED IMAGES
        # ==========================
        stored_imgs = []
        for img_list in user["user_images"]:
            stored_imgs.append(np.array(img_list, dtype=np.uint8))

        # ==========================
        # STATIC SCORE
        # ==========================
        static_score = compute_static_score(
            new_embedding,
            user["static_embeddings"],
            new_img,
            stored_imgs
        )

        # ==========================
        # DYNAMIC SCORE
        # ==========================
        dynamic_score = compute_dynamic_score(
            new_dynamic,
            user["dynamic_features"]
        )

        # ==========================
        # FUSION
        # ==========================
        final_score = 0.8 * static_score + 0.2 * dynamic_score

        threshold = float(user["threshold"])

        verified = final_score >= threshold

        os.remove(img_path)

        return {
            "verified": bool(verified),
            "static_score": round(float(static_score), 3),
            "dynamic_score": round(float(dynamic_score), 3),
            "final_score": round(float(final_score), 3),
            "threshold": round(threshold, 3)
        }, 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500