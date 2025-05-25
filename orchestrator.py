import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from dotenv import load_dotenv

# Import agents
from agents.agent_clarity import run_clarity_agent
from agents.media_scan_agent import MediaScanAgent
from agents.contextnet_agent import ContextNetAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class VerdictLevel(Enum):
    """Enum for overall verdict levels."""
    HIGH_CONFIDENCE = "High Confidence"
    MODERATE_CONFIDENCE = "Moderate Confidence"
    LOW_CONFIDENCE = "Low Confidence"
    INSUFFICIENT_DATA = "Insufficient Data"
    CONFLICTING = "Conflicting Evidence"

@dataclass
class AnalysisWeight:
    """Data class for analysis weights."""
    clarity: float = 0.4
    media: float = 0.3
    context: float = 0.3

class RealityPatchOrchestrator:
    """Main orchestrator for coordinating RealityPatch agents."""
    
    def __init__(self):
        """Initialize the orchestrator and its agents."""
        self.media_agent = MediaScanAgent()
        self.context_agent = ContextNetAgent()
        self.weights = AnalysisWeight()
        
        # Configure Gemini for clarity agent
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            logger.warning("GEMINI_API_KEY not found. Clarity analysis will be limited.")
    
    async def analyze(self, 
                     text_claim: Optional[str] = None,
                     media_path: Optional[str] = None) -> Dict:
        """
        Analyze input using appropriate agents.
        
        Args:
            text_claim: Optional text claim to analyze
            media_path: Optional path to media file to analyze
            
        Returns:
            Dict containing combined analysis results
        """
        try:
            # Validate inputs
            if not text_claim and not media_path:
                raise ValueError("At least one of text_claim or media_path must be provided")
            
            # Initialize result structure
            result = {
                "timestamp": datetime.now().isoformat(),
                "input": {
                    "text_claim": text_claim,
                    "media_path": media_path
                },
                "clarity_analysis": None,
                "media_analysis": None,
                "context_analysis": None,
                "overall_verdict": None,
                "confidence_score": 0.0,
                "verdict_level": VerdictLevel.INSUFFICIENT_DATA.value,
                "analysis_weights": {
                    "clarity": self.weights.clarity,
                    "media": self.weights.media,
                    "context": self.weights.context
                }
            }
            
            # Create tasks for parallel processing
            tasks = []
            
            # Add text analysis tasks if text is provided
            if text_claim:
                tasks.extend([
                    self._analyze_clarity(text_claim),
                    self._analyze_context(text_claim)
                ])
            
            # Add media analysis task if media is provided
            if media_path:
                tasks.append(self._analyze_media(media_path))
            
            # Wait for all tasks to complete
            if tasks:
                analyses = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for analysis in analyses:
                    if isinstance(analysis, Exception):
                        logger.error(f"Analysis failed: {str(analysis)}")
                        continue
                    
                    if "clarity" in analysis:
                        result["clarity_analysis"] = analysis["clarity"]
                    if "media" in analysis:
                        result["media_analysis"] = analysis["media"]
                    if "context" in analysis:
                        result["context_analysis"] = analysis["context"]
            
            # Calculate overall verdict and confidence
            verdict_data = self._calculate_overall_verdict(result)
            result.update(verdict_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in analysis: {str(e)}")
            return {
                "error": str(e),
                "status": "failed",
                "verdict_level": VerdictLevel.INSUFFICIENT_DATA.value
            }
    
    async def _analyze_clarity(self, text: str) -> Dict:
        """Run clarity check analysis on text."""
        try:
            if not self.gemini_api_key:
                return {
                    "clarity": {
                        "error": "GEMINI_API_KEY not found",
                        "status": "failed",
                        "confidence": 0.0
                    }
                }
            
            # Initialize Gemini model
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
            
            # Run clarity analysis
            result = await run_clarity_agent(text, model)
            
            # Calculate confidence based on claim structure and clarity
            confidence = self._calculate_clarity_confidence(result)
            
            return {
                "clarity": {
                    "claims": result,
                    "confidence": confidence,
                    "status": "success"
                }
            }
            
        except Exception as e:
            logger.error(f"Error in clarity analysis: {str(e)}")
            return {
                "clarity": {
                    "error": str(e),
                    "status": "failed",
                    "confidence": 0.0
                }
            }
    
    def _calculate_clarity_confidence(self, claims: List[Dict]) -> float:
        """Calculate confidence score for clarity analysis."""
        if not claims:
            return 0.0
        
        # Factors affecting confidence:
        # 1. Number of claims (more claims = higher confidence)
        # 2. Claim specificity (more specific = higher confidence)
        # 3. Claim structure (well-formed = higher confidence)
        
        base_confidence = min(len(claims) * 0.2, 0.8)  # Cap at 0.8
        
        # Adjust for claim specificity and structure
        specificity_scores = []
        for claim in claims:
            # Check for specific elements in claim
            has_subject = bool(claim.get("subject"))
            has_predicate = bool(claim.get("predicate"))
            has_object = bool(claim.get("object"))
            has_quantifier = bool(claim.get("quantifier"))
            
            # Calculate specificity score
            specificity = sum([
                has_subject * 0.3,
                has_predicate * 0.3,
                has_object * 0.3,
                has_quantifier * 0.1
            ])
            specificity_scores.append(specificity)
        
        # Average specificity adjustment
        specificity_adjustment = sum(specificity_scores) / len(specificity_scores)
        
        return min(base_confidence + (specificity_adjustment * 0.2), 1.0)
    
    async def _analyze_media(self, media_path: str) -> Dict:
        """Run media analysis on image/video."""
        try:
            # Validate media path
            if not os.path.exists(media_path):
                raise FileNotFoundError(f"Media file not found: {media_path}")
            
            result = await self.media_agent.analyze_media(media_path)
            return {"media": result}
            
        except Exception as e:
            logger.error(f"Error in media analysis: {str(e)}")
            return {
                "media": {
                    "error": str(e),
                    "status": "failed",
                    "confidence_score": 0.0
                }
            }
    
    async def _analyze_context(self, text: str) -> Dict:
        """Run context analysis on text."""
        try:
            result = await self.context_agent.analyze_context(text)
            return {"context": result}
            
        except Exception as e:
            logger.error(f"Error in context analysis: {str(e)}")
            return {
                "context": {
                    "error": str(e),
                    "status": "failed",
                    "confidence_bias": 0.0
                }
            }
    
    def _calculate_overall_verdict(self, result: Dict) -> Dict:
        """Calculate overall verdict based on all analyses."""
        verdicts = []
        weighted_scores = []
        conflicts = []
        
        # Process clarity analysis
        if result["clarity_analysis"] and result["clarity_analysis"].get("status") == "success":
            clarity_confidence = result["clarity_analysis"].get("confidence", 0.0)
            weighted_scores.append(clarity_confidence * self.weights.clarity)
            if clarity_confidence > 0.6:
                verdicts.append("Has verifiable claims")
        
        # Process media analysis
        if result["media_analysis"] and result["media_analysis"].get("status") == "success":
            media_confidence = result["media_analysis"].get("confidence_score", 0.0)
            weighted_scores.append(media_confidence * self.weights.media)
            if "verdict" in result["media_analysis"]:
                verdicts.append(f"Media: {result['media_analysis']['verdict']}")
        
        # Process context analysis
        if result["context_analysis"] and result["context_analysis"].get("status") == "success":
            context_confidence = result["context_analysis"].get("confidence_bias", 0.0)
            weighted_scores.append(context_confidence * self.weights.context)
            if "bias" in result["context_analysis"]:
                verdicts.append(f"Bias: {result['context_analysis']['bias']}")
        
        # Calculate overall confidence
        overall_confidence = sum(weighted_scores) if weighted_scores else 0.0
        
        # Determine verdict level
        if not weighted_scores:
            verdict_level = VerdictLevel.INSUFFICIENT_DATA
        elif overall_confidence >= 0.8:
            verdict_level = VerdictLevel.HIGH_CONFIDENCE
        elif overall_confidence >= 0.6:
            verdict_level = VerdictLevel.MODERATE_CONFIDENCE
        elif overall_confidence >= 0.4:
            verdict_level = VerdictLevel.LOW_CONFIDENCE
        else:
            verdict_level = VerdictLevel.INSUFFICIENT_DATA
        
        # Check for conflicts
        if len(verdicts) > 1:
            if any("Media: Manipulated" in v for v in verdicts) and any("Has verifiable claims" in v for v in verdicts):
                conflicts.append("Conflicting evidence between media authenticity and claim verifiability")
        
        return {
            "overall_verdict": " | ".join(verdicts) if verdicts else "Insufficient data",
            "confidence_score": overall_confidence,
            "verdict_level": verdict_level.value,
            "conflicts": conflicts if conflicts else None
        }

async def main():
    """Example usage of the RealityPatch orchestrator."""
    orchestrator = RealityPatchOrchestrator()
    
    # Test with sample inputs
    result = await orchestrator.analyze(
        text_claim="The government's new climate policy will increase energy costs by 30%",
        media_path="path/to/sample_image.jpg"
    )
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 