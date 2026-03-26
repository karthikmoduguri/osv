import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from services.dynamic_matcher import compute_dynamic_score


def compute_threshold(static_embeddings, dynamic_features, alpha=0.7):

    pair_scores = []

    for i in range(len(static_embeddings)):
        for j in range(i + 1, len(static_embeddings)):

            # static similarity
            d = np.linalg.norm(
                np.array(static_embeddings[i]) -
                np.array(static_embeddings[j])
            )

            S_static = np.exp(-d)

            # dynamic similarity
            Dynamic_Score = compute_dynamic_score(
                dynamic_features[i],
                [dynamic_features[j]]
            )

            Final = alpha * S_static + (1 - alpha) * Dynamic_Score

            pair_scores.append(Final)

    pair_scores = np.array(pair_scores)

    mean = np.mean(pair_scores)
    std = np.std(pair_scores)

    # slightly stricter threshold
    threshold = mean - (0.8 * std)

    return float(threshold)