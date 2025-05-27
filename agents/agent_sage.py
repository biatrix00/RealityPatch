import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_sage_agent(claim: str, evidence: List[Dict], model=None) -> Dict:
    """
    Run the Sage agent to provide additional analysis and context for claims.
    
    Args:
        claim: The claim to analyze
        evidence: List of evidence dictionaries
        model: Optional Gemini model instance
        
    Returns:
        Dict containing analysis results
    """
    try:
        # Initialize Gemini if not provided
        if not model:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.error("GEMINI_API_KEY not found")
                return {
                    "status": "Error",
                    "confidence": 0.0,
                    "explanation": "API key not found"
                }
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        
        # Prepare evidence for analysis
        evidence_text = "\n".join([
            f"Source: {e.get('source', 'Unknown')}\n"
            f"Content: {e.get('snippet', 'No content')}\n"
            for e in evidence
        ])
        
        # Create prompt for analysis
        prompt = f"""
        Analyze this claim and its supporting evidence to provide additional context and insights.
        
        Claim: {claim}
        
        Evidence:
        {evidence_text}
        
        Please provide:
        1. A confidence score (0-1) for the claim's validity
        2. A detailed explanation of your reasoning
        3. Any potential biases or limitations in the evidence
        4. Additional context that might be relevant
        
        Format your response as a JSON object with these fields:
        - confidence: number (0-1)
        - explanation: string
        - limitations: string[]
        - context: string
        """
        
        # Get AI analysis
        response = model.generate_content(prompt)
        
        try:
            # Parse the response as JSON
            analysis = json.loads(response.text)
            
            # Ensure all required fields exist
            result = {
                "status": "Analyzed",
                "confidence": float(analysis.get("confidence", 0.0)),
                "explanation": analysis.get("explanation", "No explanation provided"),
                "limitations": analysis.get("limitations", []),
                "context": analysis.get("context", "No additional context provided"),
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except json.JSONDecodeError:
            logger.error("Failed to parse Sage agent response as JSON")
            return {
                "status": "Error",
                "confidence": 0.0,
                "explanation": "Failed to parse analysis results",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error in Sage agent: {str(e)}")
        return {
            "status": "Error",
            "confidence": 0.0,
            "explanation": f"Error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Test the agent
    test_claim = "The Earth is flat"
    test_evidence = [
        {
            "source": "NASA",
            "snippet": "Multiple independent measurements confirm Earth is an oblate spheroid."
        }
    ]
    
    result = run_sage_agent(test_claim, test_evidence)
    print(json.dumps(result, indent=2)) 