import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Layer

# SAME CLASS AGAIN (must define to load model)
class L2Normalize(Layer):
    def call(self, inputs):
        return tf.nn.l2_normalize(inputs, axis=1)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "model", "final_signature_embedding_model.keras")
)

model = tf.keras.models.load_model(
    MODEL_PATH,
    custom_objects={"L2Normalize": L2Normalize}
)

IMG_SIZE = 96


def advanced_preprocess(img, IMG_SIZE=96):
    

    # ==========================
    # STEP 1: grayscale
    # ==========================
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # ==========================
    # STEP 2: slight blur (smooth edges)
    # ==========================
    img = cv2.GaussianBlur(img, (3, 3), 0)

    # ==========================
    # STEP 3: adaptive threshold (better than fixed 200)
    # ==========================
    th = cv2.adaptiveThreshold(
        img,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        11,
        2
    )

    # ==========================
    # STEP 4: mild dilation (restore thickness)
    # ==========================
    kernel = np.ones((2, 2), np.uint8)
    th = cv2.dilate(th, kernel, iterations=1)

    # ==========================
    # STEP 5: crop bounding box
    # ==========================
    coords = cv2.findNonZero(th)

    if coords is not None:
        x, y, w, h = cv2.boundingRect(coords)
        th = th[y:y+h, x:x+w]

    # ==========================
    # STEP 6: pad to square
    # ==========================
    h, w = th.shape
    size = max(h, w)

    square = np.ones((size, size), dtype=np.uint8) * 0  # black bg

    y_offset = (size - h) // 2
    x_offset = (size - w) // 2

    square[y_offset:y_offset+h, x_offset:x_offset+w] = th

    # ==========================
    # STEP 7: resize
    # ==========================
    square = cv2.resize(square, (IMG_SIZE, IMG_SIZE))

    # ==========================
    # STEP 8: invert (match GPDS style)
    # ==========================
    square = 255 - square

    # ==========================
    # STEP 9: RGB + normalize
    # ==========================
    square = cv2.cvtColor(square, cv2.COLOR_GRAY2RGB)
    square = square.astype("float32") / 255.0

    return np.expand_dims(square, axis=0)


def preprocess(img):

    # ==========================
    # STEP 1: binarize
    # ==========================
    _, th = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY_INV)

    # ==========================
    # STEP 2: find signature area
    # ==========================
    coords = cv2.findNonZero(th)

    if coords is not None:
        x, y, w, h = cv2.boundingRect(coords)
        img = img[y:y+h, x:x+w]

    # ==========================
    # STEP 3: pad to square
    # ==========================
    h, w = img.shape
    size = max(h, w)

    square = np.ones((size, size), dtype=np.uint8) * 255

    y_offset = (size - h) // 2
    x_offset = (size - w) // 2

    square[y_offset:y_offset+h, x_offset:x_offset+w] = img

    # ==========================
    # STEP 4: resize
    # ==========================
    square = cv2.resize(square, (IMG_SIZE, IMG_SIZE))

    # ==========================
    # STEP 5: convert to RGB
    # ==========================
    square = cv2.cvtColor(square, cv2.COLOR_GRAY2RGB)

    square = square.astype("float32") / 255.0

    return np.expand_dims(square, axis=0)

def get_embedding(image_path):

    print(f"\n[GET_EMBEDDING] Processing image: {image_path}")
    
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

    if img is None:
        raise ValueError("Invalid image")
    
    print(f"   Initial shape: {img.shape if img is not None else 'None'}")

    # If RGBA (4 channels)
    if len(img.shape) == 3 and img.shape[2] == 4:
        # Convert transparent background to white
        alpha = img[:, :, 3]
        rgb = img[:, :, :3]

        # White background
        white_bg = np.ones_like(rgb, dtype=np.uint8) * 255

        mask = alpha > 0
        white_bg[mask] = rgb[mask]

        img = cv2.cvtColor(white_bg, cv2.COLOR_BGR2GRAY)

    else:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    print(f"   After grayscale conversion: shape={img.shape}, min={np.min(img)}, max={np.max(img)}")

    img = preprocess(img)
    cv2.imwrite("debug_processed.png", (img[0] * 255).astype("uint8"))
    print(f"   After preprocessing: shape={img.shape}, min={np.min(img):.4f}, max={np.max(img):.4f}, mean={np.mean(img):.4f}")
    
    emb = model.predict(img, verbose=0)[0]
    
    print(f"   Embedding generated: shape={emb.shape}, min={np.min(emb):.6f}, max={np.max(emb):.6f}, norm={np.linalg.norm(emb):.6f}")

    return emb.tolist()