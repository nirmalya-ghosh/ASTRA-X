"""
AstraX Engine — Advanced Multi-Model Ensemble Anomaly Detection
Runs 5 independent ML models on tabular data and uses consensus voting.
Memory-safe: processes data in chunks of 200,000 rows.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging

logger = logging.getLogger("astrax.engine.detection.data")


def _run_isolation_forest(scaled_data: np.ndarray) -> np.ndarray:
    """IsolationForest: Tree-based anomaly isolation."""
    from sklearn.ensemble import IsolationForest
    clf = IsolationForest(
        contamination=0.005, random_state=42, n_jobs=1,
        n_estimators=100, max_samples='auto'
    )
    preds = clf.fit_predict(scaled_data)
    return preds == -1  # True = anomaly


def _run_local_outlier_factor(scaled_data: np.ndarray) -> np.ndarray:
    """LocalOutlierFactor: Density-based local anomaly detection."""
    from sklearn.neighbors import LocalOutlierFactor
    clf = LocalOutlierFactor(
        n_neighbors=20, contamination=0.005, n_jobs=1, novelty=False
    )
    preds = clf.fit_predict(scaled_data)
    return preds == -1


def _run_elliptic_envelope(scaled_data: np.ndarray) -> np.ndarray:
    """EllipticEnvelope: Gaussian distribution-based outlier detection."""
    from sklearn.covariance import EllipticEnvelope
    try:
        # EllipticEnvelope requires more samples than features
        if scaled_data.shape[0] < scaled_data.shape[1] * 2:
            return np.zeros(scaled_data.shape[0], dtype=bool)
        clf = EllipticEnvelope(contamination=0.005, random_state=42, support_fraction=0.9)
        preds = clf.fit_predict(scaled_data)
        return preds == -1
    except Exception:
        # Can fail on singular covariance matrices
        return np.zeros(scaled_data.shape[0], dtype=bool)


def _run_sgd_one_class_svm(scaled_data: np.ndarray) -> np.ndarray:
    """SGDOneClassSVM: Linear approximation of OneClassSVM using SGD."""
    from sklearn.linear_model import SGDOneClassSVM
    try:
        clf = SGDOneClassSVM(nu=0.005, random_state=42, max_iter=1000, tol=1e-4)
        clf.fit(scaled_data)
        preds = clf.predict(scaled_data)
        return preds == -1
    except Exception:
        return np.zeros(scaled_data.shape[0], dtype=bool)


def _run_zscore_outlier(scaled_data: np.ndarray, threshold: float = 3.5) -> np.ndarray:
    """Z-Score Statistical Outlier: Classical sigma-clipping across all features."""
    # For each feature, compute z-score. A row is anomalous if ANY feature exceeds threshold.
    z_scores = np.abs(scaled_data)  # Already standardized, so values ARE z-scores
    max_z_per_row = np.max(z_scores, axis=1)
    return max_z_per_row > threshold


MODEL_REGISTRY = {
    "IsolationForest": _run_isolation_forest,
    "LocalOutlierFactor": _run_local_outlier_factor,
    "EllipticEnvelope": _run_elliptic_envelope,
    "SGDOneClassSVM": _run_sgd_one_class_svm,
    "ZScoreOutlier": _run_zscore_outlier,
}


def detect_data_anomalies(file_path: str, z_thresh: float = 3.0) -> List[Dict[str, Any]]:
    """
    Detect statistical outliers in a tabular dataset using a 5-model ensemble.
    Each model independently votes on anomaly status.
    A row is flagged if >= 2 out of 5 models agree it is anomalous.
    Returns rows with consensus anomaly scores.
    """
    try:
        from sklearn.preprocessing import StandardScaler

        sources = []
        chunk_size = 200000
        global_row_offset = 0
        total_models = len(MODEL_REGISTRY)

        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            numeric_cols = chunk.select_dtypes(include=[np.number]).columns

            if len(numeric_cols) == 0:
                global_row_offset += len(chunk)
                continue

            # Handle missing values
            chunk_numeric = chunk[numeric_cols].fillna(chunk[numeric_cols].median())

            # Drop columns with zero variance (causes issues for some models)
            nonzero_var = chunk_numeric.columns[chunk_numeric.std() > 1e-10]
            if len(nonzero_var) == 0:
                global_row_offset += len(chunk)
                continue
            chunk_numeric = chunk_numeric[nonzero_var]

            # Scale features
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(chunk_numeric)

            # Run all models and collect votes
            vote_matrix = np.zeros((len(chunk), total_models), dtype=bool)

            for i, (model_name, model_fn) in enumerate(MODEL_REGISTRY.items()):
                try:
                    vote_matrix[:, i] = model_fn(scaled_data)
                    n_flagged = int(np.sum(vote_matrix[:, i]))
                    logger.info(f"  {model_name}: flagged {n_flagged}/{len(chunk)} rows")
                except Exception as e:
                    logger.warning(f"  {model_name} failed: {e}")

            # Consensus: count how many models flagged each row
            vote_counts = np.sum(vote_matrix, axis=1)

            # Require at least 2 models to agree
            min_votes = 2
            consensus_mask = vote_counts >= min_votes

            anomalous_indices = np.where(consensus_mask)[0]

            for local_idx in anomalous_indices:
                global_idx = global_row_offset + local_idx
                row = chunk.iloc[local_idx]

                # Confidence = fraction of models that agree (0.4 to 1.0)
                n_votes = int(vote_counts[local_idx])
                confidence = n_votes / total_models

                # Build model agreement string
                agreed_models = []
                for j, model_name in enumerate(MODEL_REGISTRY.keys()):
                    if vote_matrix[local_idx, j]:
                        agreed_models.append(model_name)

                # Extract key features for the notes
                flux_val = float(row.get('absolute_magnitude', row.iloc[0]) if 'absolute_magnitude' in row.index else 1.0)
                diameter_val = float(row.get('est_diameter_max', row.get('estimated_diameter.kilometers.estimated_diameter_max', 1.0)))

                sources.append({
                    "x": float(global_idx),
                    "y": 0.0,
                    "flux": flux_val,
                    "mag": diameter_val,
                    "snr": confidence * 100.0,  # Use confidence as SNR proxy
                    "confidence_score": round(confidence, 4),
                    "detection_method": f"ensemble({','.join(agreed_models)})",
                    "notes": (
                        f"Ensemble Detection: {n_votes}/{total_models} models agree this is anomalous "
                        f"(Row {global_idx}). "
                        f"Models: {', '.join(agreed_models)}. "
                        f"Confidence: {confidence*100:.0f}%."
                    ),
                })

            global_row_offset += len(chunk)

        logger.info(
            f"Multi-model ensemble found {len(sources)} consensus anomalies "
            f"across {global_row_offset} rows in {file_path}"
        )
        return sources

    except Exception as e:
        logger.error(f"Ensemble data detection failed: {e}", exc_info=True)
        return []
