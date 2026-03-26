



import numpy as np
import cv2
from skimage.metrics import structural_similarity as ssim


# ==============================
# SHAPE FEATURE: HU MOMENTS
# ==============================
def get_hu_moments(img):
    moments = cv2.moments(img)
    hu = cv2.HuMoments(moments).flatten()
    return hu


# ==============================
# SHAPE SCORE
# ==============================
def compute_shape_score(img1, img2):

    import cv2
    import numpy as np

    # ======================
    # BINARIZE
    # ======================
    _, b1 = cv2.threshold(img1, 127, 255, cv2.THRESH_BINARY_INV)
    _, b2 = cv2.threshold(img2, 127, 255, cv2.THRESH_BINARY_INV)

    # ======================
    # CENTER + CROP
    # ======================
    def normalize(b):
        coords = cv2.findNonZero(b)
        if coords is not None:
            x, y, w, h = cv2.boundingRect(coords)
            b = b[y:y+h, x:x+w]

        size = max(b.shape)
        square = np.zeros((size, size), dtype=np.uint8)

        y_off = (size - b.shape[0]) // 2
        x_off = (size - b.shape[1]) // 2

        square[y_off:y_off+b.shape[0], x_off:x_off+b.shape[1]] = b

        return cv2.resize(square, (96, 96))

    b1 = normalize(b1)
    b2 = normalize(b2)

    # ======================
    # DISTANCE TRANSFORM
    # ======================
    dist = cv2.distanceTransform(255 - b2, cv2.DIST_L2, 3)

    # normalize distance
    dist = dist / (dist.max() + 1e-6)

    # ======================
    # MATCH SCORE
    # ======================
    points = np.where(b1 > 0)

    if len(points[0]) == 0:
        return 0.0

    values = dist[points]

    # lower distance = better match
    score = 1.0 - np.mean(values)

    return float(score)


# ==============================
# STATIC SCORE (MAIN FUNCTION)
# ==============================
def compute_static_score(new_embedding, stored_embeddings,
                         new_img, stored_imgs):

    if not stored_embeddings:
        return 0.0

    new_embedding = np.array(new_embedding)

    emb_scores = []
    shape_scores = []

    print("\n[STATIC DEBUG]")

    for i, emb in enumerate(stored_embeddings):

        emb = np.array(emb)

        # ----------------------
        # EMBEDDING DISTANCE
        # ----------------------
        d = np.linalg.norm(new_embedding - emb)
        emb_score = np.exp(-d)

        emb_scores.append(emb_score)

        # ----------------------
        # SHAPE SCORE
        # ----------------------
        shape_score = compute_shape_score(
            new_img, stored_imgs[i]
        )

        shape_scores.append(shape_score)

        print(f"[{i}] dist={d:.4f} | emb={emb_score:.4f} | shape={shape_score:.4f}")

    # ======================
    # TOP-K STRATEGY
    # ======================
    top_k = 3

    emb_top = sorted(emb_scores, reverse=True)[:top_k]
    shape_top = sorted(shape_scores, reverse=True)[:top_k]

    emb_final = np.mean(emb_top)
    shape_final = np.mean(shape_top)

    # ======================
    # FINAL STATIC SCORE
    # ======================
    final_static = 0.3 * emb_final + 0.7 * shape_final

    print("\n[STATIC FINAL]")
    print(f"Embedding Score : {emb_final:.4f}")
    print(f"Shape Score     : {shape_final:.4f}")
    print(f"Final Static    : {final_static:.4f}")

    return float(final_static)