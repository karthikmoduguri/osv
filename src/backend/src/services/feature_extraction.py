import numpy as np

def extract_physics_features_from_strokes(strokes):
    # flatten strokes
    points = [p for stroke in strokes for p in stroke]
   # print(strokes,"hi")
    if len(points) < 6:
        return None

    x = np.array([p["x"] for p in points])
    y = np.array([p["y"] for p in points])
    t = np.array([p["time"] for p in points])

    dx = np.diff(x)
    dy = np.diff(y)
    dt = np.diff(t)
    dt[dt == 0] = 1

    # Velocity
    v = np.sqrt(dx**2 + dy**2) / dt

    # Acceleration
    a = np.diff(v) / dt[1:]

    # Direction
    theta = np.arctan2(dy, dx)

    # Angular velocity
    w = np.diff(theta) / dt[1:]

    # Angular acceleration
    alpha = np.diff(w) / dt[2:]

    # Simulated pressure
    pressure = 1 / (v + 1e-6)

    # Torque proxy
    tau = pressure * v

    def stats(arr):
        return [np.mean(arr), np.std(arr), np.max(arr)]

    stroke_count = np.sum(dt > np.percentile(dt, 90)) + 1
    direction_changes = np.sum(np.abs(np.diff(theta)) > np.pi / 4)

    feature_vector = (
        stats(v) +
        stats(a) +
        stats(w)[:2] +
        stats(alpha)[:2] +
        stats(tau) +
        [stroke_count, direction_changes]
    )

    return feature_vector
