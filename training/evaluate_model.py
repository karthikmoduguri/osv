import os
import re
import cv2
import random
import numpy as np
import joblib
import tensorflow as tf

from itertools import combinations
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    classification_report,
    roc_auc_score
)
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import load_model
from tensorflow.keras import layers

# ==========================================
# CUSTOM LAYER (FOR MODEL LOADING)
# ==========================================

class L2Normalize(layers.Layer):
    def call(self, inputs):
        return tf.nn.l2_normalize(inputs, axis=1)

# ==========================================
# CONFIG
# ==========================================

DATA_PATH = r"D:\clg resumes\osv-hybrid (2)\osv-hybrid\training\New folder (10)\train"
IMG_SIZE = 96

STATIC_MODEL_PATH = r"D:\clg resumes\osv-hybrid (2)\osv-hybrid\src\backend\model\final_signature_embedding_model.keras"
RF_MODEL_PATH = r"D:\clg resumes\osv-hybrid (2)\osv-hybrid\src\backend\model\rf_model.pkl"

W1, W2 = 0.7, 0.3
INTER_USER_NEG = 20

# ==========================================
# LOAD MODELS
# ==========================================

print("Loading models...")

embedding_model = load_model(
    STATIC_MODEL_PATH,
    custom_objects={"L2Normalize": L2Normalize}
)

rf_model = joblib.load(RF_MODEL_PATH)

print("Models loaded successfully.")

# ==========================================
# IMAGE LOADER
# ==========================================

def load_image(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    img = img.astype("float32") / 255.0
    return img

# ==========================================
# UID EXTRACTOR
# ==========================================

def get_uid(filename):
    name = os.path.splitext(filename)[0]
    m = re.search(r'c-(\d+)-', name.lower())
    if m:
        return m.group(1).zfill(3)
    return None

# ==========================================
# BUILD PAIRS
# ==========================================

genuine_path = os.path.join(DATA_PATH, "genuine")
forge_path = os.path.join(DATA_PATH, "forge")

genuine_files = os.listdir(genuine_path)
forge_files = os.listdir(forge_path)

user_genuine = {}
user_forge = {}

for f in genuine_files:
    uid = get_uid(f)
    if uid:
        user_genuine.setdefault(uid, []).append(f)

for f in forge_files:
    uid = get_uid(f)
    if uid:
        user_forge.setdefault(uid, []).append(f)

pairs = []
users = list(user_genuine.keys())

for uid in users:
    g_list = user_genuine[uid]
    f_list = user_forge.get(uid, [])

    # Genuine-Genuine (positive)
    for g1, g2 in combinations(g_list, 2):
        pairs.append((
            os.path.join(genuine_path, g1),
            os.path.join(genuine_path, g2),
            1
        ))

    # Genuine-Forgery (negative)
    for g in g_list:
        for f in f_list:
            pairs.append((
                os.path.join(genuine_path, g),
                os.path.join(forge_path, f),
                0
            ))

# 🔥 Add inter-user negatives (VERY IMPORTANT)
for _ in range(len(users) * INTER_USER_NEG):
    u1, u2 = random.sample(users, 2)
    g1 = random.choice(user_genuine[u1])
    g2 = random.choice(user_genuine[u2])

    pairs.append((
        os.path.join(genuine_path, g1),
        os.path.join(genuine_path, g2),
        0
    ))

# ==========================================
# CHECK LABEL DISTRIBUTION
# ==========================================

labels = [p[2] for p in pairs]
print("Full dataset label distribution:", np.unique(labels, return_counts=True))

# Stratified split (IMPORTANT)
train_pairs, val_pairs = train_test_split(
    pairs,
    test_size=0.2,
    random_state=42,
    stratify=labels
)

val_labels = [p[2] for p in val_pairs]
print("Validation label distribution:", np.unique(val_labels, return_counts=True))

print("Validation pairs:", len(val_pairs))

# ==========================================
# FAST EMBEDDING
# ==========================================

print("Preparing validation images...")

all_images = []
pair_indices = []
y_true = []

for idx, (p1, p2, label) in enumerate(val_pairs):

    img1 = load_image(p1)
    img2 = load_image(p2)

    all_images.append(img1)
    all_images.append(img2)

    pair_indices.append((2 * idx, 2 * idx + 1))
    y_true.append(label)

all_images = np.array(all_images)
y_true = np.array(y_true)

print("Total images for embedding:", len(all_images))

print("Computing embeddings in batch...")
embeddings = embedding_model.predict(all_images, batch_size=64, verbose=1)

static_scores = []
fusion_scores = []

for (i1, i2), label in zip(pair_indices, y_true):

    e1 = embeddings[i1]
    e2 = embeddings[i2]

    static_dist = np.linalg.norm(e1 - e2)
    static_score = 1 / (1 + static_dist)

    dynamic_score = static_score  # replace later with real dynamic pair score

    fusion_score = (W1 * static_score) + (W2 * dynamic_score)

    static_scores.append(static_score)
    fusion_scores.append(fusion_score)

static_scores = np.array(static_scores)
fusion_scores = np.array(fusion_scores)

# ==========================================
# EVALUATION FUNCTION
# ==========================================

def evaluate_scores(scores, name):

    best_acc = 0
    best_thresh = 0

    for t in np.linspace(0, 1, 200):
        preds = (scores >= t).astype(int)
        acc = accuracy_score(y_true, preds)
        if acc > best_acc:
            best_acc = acc
            best_thresh = t

    final_preds = (scores >= best_thresh).astype(int)

    print(f"\n====== {name} RESULTS ======")
    print("Best Threshold:", round(best_thresh, 3))
    print("Accuracy:", round(best_acc, 4))
    print("AUC:", round(roc_auc_score(y_true, scores), 4))
    print("Confusion Matrix:\n", confusion_matrix(y_true, final_preds))
    print(classification_report(y_true, final_preds))

# ==========================================
# RUN
# ==========================================

evaluate_scores(static_scores, "STATIC")
evaluate_scores(fusion_scores, "HYBRID")