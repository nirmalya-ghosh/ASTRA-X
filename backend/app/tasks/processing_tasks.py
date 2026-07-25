import logging
import time
from app.tasks.celery_app import celery_app
from astrax_engine.processing.pipeline import ProcessingPipeline
from astrax_engine.detection.candidates import link_candidates
import numpy as np
import asyncio

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.processing_tasks.run_processing_pipeline")
def run_processing_pipeline(self, dataset_id: int, pipeline_config: list, params: dict):
    """
    Run the processing pipeline on a dataset.
    This task updates its state so WebSockets can stream progress.
    """
    try:
        logger.info(f"Starting pipeline for dataset {dataset_id}")
        self.update_state(state="PROGRESS", meta={"progress": 0, "status": "Initializing pipeline..."})
        
        # Simulated workload (since we don't have DB connected in this Celery worker yet)
        # In a real scenario, we'd fetch frames from the dataset
        total_frames = params.get("total_frames", 10)
        
        # Build the engine pipeline
        pipeline = ProcessingPipeline(steps=pipeline_config)
        
        for i in range(total_frames):
            self.update_state(
                state="PROGRESS", 
                meta={
                    "progress": int((i / total_frames) * 100), 
                    "status": f"Processing frame {i+1}/{total_frames}"
                }
            )
            # Mocking frame processing
            mock_data = np.random.normal(100, 10, (1024, 1024))
            _ = pipeline.process_frame(mock_data)
            time.sleep(0.5) # simulate work
            
        self.update_state(state="PROGRESS", meta={"progress": 100, "status": "Pipeline complete!"})
        return {"status": "success", "processed_frames": total_frames}
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise e
