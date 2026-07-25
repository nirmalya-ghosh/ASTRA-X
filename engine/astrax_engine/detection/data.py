"""
AstraX Engine — Data Detection
Local algorithmic anomaly detection for tabular data (CSV/JSON) using statistical outliers.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging

logger = logging.getLogger("astrax.engine.detection.data")

def detect_data_anomalies(file_path: str, z_thresh: float = 3.0) -> List[Dict[str, Any]]:
    """
    Detect statistical outliers in a tabular dataset (e.g. Kaggle NASA asteroid data).
    Returns rows that appear highly anomalous.
    """
    try:
        df = pd.read_csv(file_path)
        
        # Select numeric columns for anomaly detection
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) == 0:
            logger.warning("No numeric columns found for anomaly detection")
            return []
            
        # Handle missing values by filling with median
        df_numeric = df[numeric_cols].fillna(df[numeric_cols].median())
        
        # 1. Advanced Anomaly Detection using Isolation Forests
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
        
        # Scale the data for better isolation
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(df_numeric)
        
        # Train and predict using Isolation Forest (contamination is the expected anomaly rate, e.g. 1%)
        clf = IsolationForest(contamination=0.01, random_state=42, n_jobs=-1)
        preds = clf.fit_predict(scaled_data)
        
        # preds: -1 for anomalies, 1 for normal
        outliers = (preds == -1)
        anomalous_df = df[outliers]
        
        # Calculate Anomaly Scores (negative is more anomalous, flip it for SNR proxy)
        scores = clf.decision_function(scaled_data)
        
        sources = []
        for idx, row in anomalous_df.iterrows():
            # Invert score so higher is more anomalous for our backend ranking
            anomaly_score = abs(float(scores[df.index.get_loc(idx)])) * 10.0
            
            # Format candidate string safely
            safe_row_dict = {str(k): (float(v) if isinstance(v, (int, float)) else str(v)) for k, v in row.to_dict().items()}
            
            sources.append({
                "x": float(idx), # using row index as mock x position
                "y": 0.0,
                "flux": float(row.get('absolute_magnitude', row.iloc[0]) if 'absolute_magnitude' in row else 1.0),
                "mag": float(row.get('est_diameter_max', 1.0)), 
                "snr": anomaly_score, # Isolation score as SNR
                "notes": f"Scikit-Learn IsolationForest: Highly anomalous object detected at row {idx}."
            })
            
        logger.info(f"Scikit-Learn IsolationForest found {len(sources)} anomalies in {file_path}")
        return sources
        
    except Exception as e:
        logger.error(f"Local data detection failed: {e}")
        return []
