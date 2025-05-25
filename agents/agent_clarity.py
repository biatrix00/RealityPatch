import google.generativeai as genai
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_clarity_agent(text, model, ask_path="ask_files/clarity.ask"):
    """
    Extract claims from text and return them in a structured format.
    
    Args:
        text: The text to analyze
        model: The Gemini model instance
        ask_path: Path to the prompt template
        
    Returns:
        List of dictionaries containing structured claims
    """
    try:
        # Read the prompt template
        with open(ask_path, "r") as file:
            prompt_template = file.read()

        # Construct the full prompt with JSON formatting instructions
        full_prompt = f"""
        {prompt_template}

        For the following text, extract any factual claims or questions that can be treated as claims.
        Format them as a JSON array. Each claim should be an object with these fields:
        - subject: The main actor or entity
        - predicate: The action or state
        - object: What is being acted upon
        - quantifier: Any numerical or qualitative modifiers
        - time_reference: When the claim is about
        - location: Where the claim is about
        - source: Where the claim comes from (if mentioned)
        - confidence: Your confidence in this claim extraction (0-1)

        Examples:
        1. Input: "India broke the ceasefire"
           Output:
           [
             {{
               "subject": "India",
               "predicate": "broke",
               "object": "the ceasefire",
               "quantifier": "",
               "time_reference": "",
               "location": "",
               "source": "",
               "confidence": 0.9
             }}
           ]

        2. Input: "Is the earth flat?"
           Output:
           [
             {{
               "subject": "the earth",
               "predicate": "is",
               "object": "flat",
               "quantifier": "",
               "time_reference": "",
               "location": "",
               "source": "",
               "confidence": 0.9
             }}
           ]

        Now analyze this text:
        {text.strip()}

        Return ONLY the JSON array, nothing else.
        """
        
        # Generate response using the provided model instance
        response = model.generate_content(full_prompt)
        
        # Log the raw response for debugging
        logger.info(f"Raw response from model: {response.text}")
        
        try:
            # Clean the response text to ensure it's valid JSON
            response_text = response.text.strip()
            # Remove any markdown code block markers
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Parse the response as JSON
            claims = json.loads(response_text)
            
            # Ensure we have a list of claims
            if not isinstance(claims, list):
                claims = [claims]
            
            # Validate and clean each claim
            cleaned_claims = []
            for claim in claims:
                if isinstance(claim, dict):
                    # Ensure all required fields exist
                    cleaned_claim = {
                        "subject": claim.get("subject", ""),
                        "predicate": claim.get("predicate", ""),
                        "object": claim.get("object", ""),
                        "quantifier": claim.get("quantifier", ""),
                        "time_reference": claim.get("time_reference", ""),
                        "location": claim.get("location", ""),
                        "source": claim.get("source", ""),
                        "confidence": float(claim.get("confidence", 0.0))
                    }
                    # Log each cleaned claim
                    logger.info(f"Cleaned claim: {json.dumps(cleaned_claim, indent=2)}")
                    cleaned_claims.append(cleaned_claim)
            
            if not cleaned_claims:
                logger.warning("No valid claims were extracted from the response")
                return []
                
            return cleaned_claims
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response as JSON: {str(e)}")
            logger.error(f"Response text: {response.text}")
            # Fallback: try to extract claims from text format
            return _extract_claims_from_text(response.text)
            
    except Exception as e:
        logger.error(f"Error in clarity agent: {str(e)}")
        return []

def _extract_claims_from_text(text: str) -> list:
    """Extract claims from text format when JSON parsing fails."""
    try:
        # Split text into lines
        lines = text.strip().split('\n')
        claims = []
        
        # Process each line that looks like a claim
        for line in lines:
            line = line.strip()
            if line and not line.startswith('CLAIMS:'):
                # Try to extract basic claim components
                parts = line.split()
                if len(parts) >= 3:  # At least subject, predicate, object
                    claim = {
                        "subject": parts[0],
                        "predicate": parts[1],
                        "object": " ".join(parts[2:]),
                        "quantifier": "",
                        "time_reference": "",
                        "location": "",
                        "source": "",
                        "confidence": 0.5  # Default confidence
                    }
                    claims.append(claim)
        
        return claims
        
    except Exception as e:
        logger.error(f"Error extracting claims from text: {str(e)}")
        return []

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
    result = run_clarity_agent(test_text, model)
    print(json.dumps(result, indent=2))