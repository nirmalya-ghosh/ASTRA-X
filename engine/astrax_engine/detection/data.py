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
            
        # Calculate Z-scores
        z_scores = np.abs((df[numeric_cols] - df[numeric_cols].mean()) / df[numeric_cols].std(ddof=0))
        
        # Find rows where ANY metric exceeds threshold
        outliers = (z_scores > z_thresh).any(axis=1)
        anomalous_df = df[outliers]
        
        sources = []
        for idx, row in anomalous_df.iterrows():
            # Mock candidate format for data rows
            sources.append({
                "x": float(idx), # using row index as mock x position
                "y": 0.0,
                "flux": float(row.get('absolute_magnitude', row.iloc[0]) if 'absolute_magnitude' in row else 1.0),
                "mag": float(row.get('est_diameter_max', 1.0)), 
                "snr": float(z_scores.loc[idx].max()), # Max z-score as SNR
                "notes": f"Statistical outlier detected at row {idx}. Data: {row.to_dict()}"
            })
            
        logger.info(f"Pandas local data detection found {len(sources)} anomalies in {file_path}")
        return sources
        
    except Exception as e:
        logger.error(f"Local data detection failed: {e}")
        return []
