"""
AstraX Engine — Exporters
Export candidates and reports to various formats (CSV, JSON, PDF).
"""

import logging
import json
import csv
import io
from typing import List, Dict, Any

logger = logging.getLogger("astrax.engine.io.exporters")


def export_candidates_csv(candidates: List[Dict[str, Any]]) -> str:
    """Export candidates to CSV string."""
    if not candidates:
        return ""
        
    output = io.StringIO()
    # Extract headers from first candidate
    keys = list(candidates[0].keys())
    
    writer = csv.DictWriter(output, fieldnames=keys)
    writer.writeheader()
    for cand in candidates:
        writer.writerow(cand)
        
    return output.getvalue()


def export_candidates_json(candidates: List[Dict[str, Any]]) -> str:
    """Export candidates to JSON string."""
    return json.dumps(candidates, indent=2)


def generate_pdf_report(dataset_info: Dict[str, Any], candidates: List[Dict[str, Any]]) -> bytes:
    """
    Generate a PDF report.
    Note: Requires reportlab installed.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        width, height = letter
        
        # Header
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, height - 50, "AstraX AI Observation Report")
        
        # Dataset info
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 80, f"Dataset: {dataset_info.get('name', 'Unknown')}")
        c.drawString(50, height - 100, f"Frames: {dataset_info.get('file_count', 0)}")
        c.drawString(50, height - 120, f"Total Candidates: {len(candidates)}")
        
        # Top candidates
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 160, "Top Confirmed Candidates")
        
        c.setFont("Helvetica", 10)
        y = height - 180
        
        confirmed = [c for c in candidates if c.get('classification') == 'confirmed']
        confirmed.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        for cand in confirmed[:10]:
            if y < 50:
                c.showPage()
                y = height - 50
                
            text = f"ID: {cand.get('id')} | Score: {cand.get('confidence_score', 0):.2f} | " \
                   f"Pos: ({cand.get('x_centroid', 0):.1f}, {cand.get('y_centroid', 0):.1f}) | " \
                   f"Motion: ({cand.get('motion_dx', 0):.2f}, {cand.get('motion_dy', 0):.2f})"
            c.drawString(50, y, text)
            y -= 20
            
        c.save()
        buf.seek(0)
        return buf.read()
        
    except ImportError:
        logger.error("reportlab not installed. Cannot generate PDF report.")
        return b""
    except Exception as e:
        logger.error(f"Failed to generate PDF report: {e}")
        return b""
