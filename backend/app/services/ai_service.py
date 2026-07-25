import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AIService:
    """Mock abstract LLM Service for AstraX AI."""
    def __init__(self, provider: str = "gemini"):
        self.provider = provider
        
    async def chat(self, messages: List[Dict[str, str]]) -> str:
        """Stream a chat response from the LLM."""
        logger.info(f"AI Service (provider: {self.provider}) processing chat...")
        
        last_message = messages[-1]["content"].lower()
        if "candidate" in last_message or "explain" in last_message:
            return "Based on the detection parameters, this candidate shows strong persistence across 5 frames with a linear motion vector typical of a Main Belt asteroid. The Signal-to-Noise Ratio (SNR) of 15.2 indicates a high-confidence detection."
        elif "report" in last_message or "summarize" in last_message:
            return "Observation Session Summary:\n- 150 frames processed\n- 12 candidates detected\n- 3 high-confidence NEO candidates flagged for manual review."
        else:
            return "I am the AstraX AI Assistant. I can help you analyze candidates, explain processing steps, or draft observation reports. What would you like to know?"

    async def draft_report(self, dataset_info: dict, candidates: list) -> str:
        """Generate a scientific report based on detections."""
        logger.info("Drafting AI report...")
        report = f"# AstraX AI Preliminary Report\n\n## Dataset Overview\nAnalyzed {dataset_info.get('file_count', 0)} frames from dataset '{dataset_info.get('name', 'Unknown')}'.\n\n## Findings\nDetected {len(candidates)} moving objects.\n\n"
        
        high_conf = [c for c in candidates if c.get('confidence_score', 0) > 0.8]
        if high_conf:
            report += f"**Key Finding**: {len(high_conf)} high-confidence candidates identified with distinct linear motion trajectories."
        else:
            report += "No high-confidence candidates were identified in this session."
            
        return report

# Global AI service instance
ai_assistant = AIService()
