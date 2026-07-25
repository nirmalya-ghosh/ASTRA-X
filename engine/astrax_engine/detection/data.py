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
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
        
        sources = []
        chunk_size = 50000
        global_row_offset = 0
        
        # Read the CSV in chunks to minimize RAM usage
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            numeric_cols = chunk.select_dtypes(include=[np.number]).columns
            
            if len(numeric_cols) == 0:
                global_row_offset += len(chunk)
                continue
                
            # Handle missing values by filling with median
            chunk_numeric = chunk[numeric_cols].fillna(chunk[numeric_cols].median())
            
            # Scale the data for better isolation
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(chunk_numeric)
            
            # Train and predict using Isolation Forest locally on this chunk
            clf = IsolationForest(contamination=0.01, random_state=42, n_jobs=-1)
            preds = clf.fit_predict(scaled_data)
            
            # preds: -1 for anomalies, 1 for normal
            outliers = (preds == -1)
            anomalous_df = chunk[outliers]
            
            # Calculate Anomaly Scores
            scores = clf.decision_function(scaled_data)
            
            for local_idx, row in anomalous_df.iterrows():
                global_idx = global_row_offset + chunk.index.get_loc(local_idx)
                
                # Invert score so higher is more anomalous for our backend ranking
                anomaly_score = abs(float(scores[chunk.index.get_loc(local_idx)])) * 10.0
                
                sources.append({
                    "x": float(global_idx), # using row index as mock x position
                    "y": 0.0,
                    "flux": float(row.get('absolute_magnitude', row.iloc[0]) if 'absolute_magnitude' in row else 1.0),
                    "mag": float(row.get('est_diameter_max', 1.0)), 
                    "snr": anomaly_score, # Isolation score as SNR
                    "notes": f"Scikit-Learn IsolationForest: Highly anomalous object detected at row {global_idx}."
                })
                
            global_row_offset += len(chunk)
            
        logger.info(f"Chunked IsolationForest found {len(sources)} anomalies across {global_row_offset} rows in {file_path}")
        return sources
        
    except Exception as e:
        logger.error(f"Local data detection failed: {e}")
        return []
