import os
import google.generativeai as genai
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_clarity_agent(claim: str) -> dict:
    """
    Analyze a claim for clarity and structure using Gemini.
    
    Args:
        claim (str): The claim to analyze
        
    Returns:
        dict: Analysis results including clarity score and components
    """
    try:
        # Initialize Gemini
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        
        # Create prompt
        prompt = f"""
        Analyze the following claim for clarity and structure:
        
        Claim: {claim}
        
        Please provide:
        1. A clarity score (0-1)
        2. Breakdown of claim components (subject, predicate, qualifiers, etc.)
        3. Suggestions for improvement if needed
        
        Format the response as a JSON object with the following structure:
        {{
            "clarity_score": float,
            "components": [
                {{
                    "type": str,
                    "text": str
                }}
            ],
            "suggestions": [str],
            "original_claim": str
        }}
        """
        
        # Get response from Gemini
        response = await model.generate_content_async(prompt)
        result = response.text
        
        # Parse the response
        try:
            analysis = eval(result)  # Simple parsing for now
            analysis['timestamp'] = datetime.now().isoformat()
            return analysis
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            return {
                "clarity_score": 0.5,
                "components": [{"type": "error", "text": "Error parsing response"}],
                "suggestions": ["Please try again"],
                "original_claim": claim,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error in clarity agent: {str(e)}")
        return {
            "clarity_score": 0.5,
            "components": [{"type": "error", "text": str(e)}],
            "suggestions": ["Please try again"],
            "original_claim": claim,
            "timestamp": datetime.now().isoformat()
        }

# For testing
if __name__ == "__main__":
    test_text = "Is the earth flat?"
    
    # Initialize model
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
    
    # Run test
    result = run_clarity_agent(test_text)
    print(result)