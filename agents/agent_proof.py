import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
import aiohttp
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from .agent_sage import run_sage_agent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define reliable sources and conspiracy keywords
RELIABLE_SOURCES = {
    # Scientific and Academic
    "nasa.gov": 1.0,
    "wikipedia.org": 0.9,
    "britannica.com": 0.95,
    "scientificamerican.com": 0.9,
    "nature.com": 0.95,
    "science.org": 0.95,
    "scholar.google.com": 0.95,
    "arxiv.org": 0.95,
    "jstor.org": 0.95,
    "sciencedirect.com": 0.95,
    "researchgate.net": 0.9,
    
    # News and Media
    "reuters.com": 0.85,
    "apnews.com": 0.85,
    "bbc.com": 0.85,
    "theguardian.com": 0.85,
    "nytimes.com": 0.85,
    "washingtonpost.com": 0.85,
    "bloomberg.com": 0.85,
    "economist.com": 0.85,
    
    # Educational and Reference
    "smithsonianmag.com": 0.9,
    "nationalgeographic.com": 0.9,
    "britannica.com": 0.95,
    "history.com": 0.85,
    "worldbank.org": 0.9,
    "un.org": 0.9,
    "who.int": 0.95,
    "imf.org": 0.9,
    
    # Science and Technology
    "sciencedaily.com": 0.9,
    "phys.org": 0.9,
    "ieee.org": 0.9,
    "acm.org": 0.9,
    "springer.com": 0.9,
    "wiley.com": 0.9,
    "tandfonline.com": 0.9,
    "sage.com": 0.9
}

CONSPIRACY_KEYWORDS = {
    "flat earth": -0.8,
    "hollow earth": -0.8,
    "fake moon landing": -0.8,
    "vaccines cause autism": -0.8,
    "chemtrails": -0.8,
    "lizard people": -0.8,
    "illuminati": -0.7,
    "new world order": -0.7,
    "deep state": -0.7,
    "fake news": -0.6,
    "conspiracy": -0.6,
    "cover up": -0.6,
    "they're hiding": -0.6,
    "secret society": -0.6,
    "global elite": -0.6,
    "aliens control": -0.8,
    "shadow government": -0.7,
    "mind control": -0.7
}

COMMON_KNOWLEDGE = {
    "sky is blue": 0.95,
    "water is wet": 0.95,
    "earth is round": 0.95,
    "earth is an oblate spheroid": 0.95,
    "sun rises in east": 0.95,
    "humans need oxygen": 0.95,
    "gravity exists": 0.95,
    "moon orbits earth": 0.95,
    "earth orbits sun": 0.95
}

def get_source_reliability(url: str) -> float:
    """Calculate source reliability score based on domain"""
    for domain, score in RELIABLE_SOURCES.items():
        if domain in url.lower():
            return score
    return 0.5  # Default score for unknown sources

def check_conspiracy_keywords(claim: str) -> float:
    """Check for conspiracy keywords and return confidence penalty"""
    claim_lower = claim.lower()
    max_penalty = 0.0
    for keyword, penalty in CONSPIRACY_KEYWORDS.items():
        if keyword in claim_lower:
            max_penalty = min(max_penalty, penalty)  # Take the most negative penalty
    return max_penalty

def check_common_knowledge(claim: str) -> float:
    """Check if claim is common knowledge and return confidence boost"""
    claim_lower = claim.lower()
    for phrase, score in COMMON_KNOWLEDGE.items():
        if phrase in claim_lower:
            return score
    return 0.0

def analyze_evidence_quality(evidence: List[Dict]) -> Tuple[float, float]:
    """Analyze evidence quality and return (support_score, contradiction_score)"""
    if not evidence:
        return 0.0, 0.0
    
    support_score = 0.0
    contradiction_score = 0.0
    
    # Keywords indicating support or contradiction
    support_keywords = ["confirm", "verify", "prove", "evidence shows", "research shows", "study shows", "scientists agree"]
    contradiction_keywords = ["debunk", "false", "myth", "hoax", "conspiracy", "disprove", "refute"]
    
    for e in evidence:
        snippet = e.get("snippet", "").lower()
        source_score = e.get("reliability", 0.5)
        
        # Check for support
        for keyword in support_keywords:
            if keyword in snippet:
                support_score += source_score
                break
        
        # Check for contradiction
        for keyword in contradiction_keywords:
            if keyword in snippet:
                contradiction_score += source_score
                break
    
    # Normalize scores
    total_evidence = len(evidence)
    if total_evidence > 0:
        support_score = min(1.0, support_score / total_evidence)
        contradiction_score = min(1.0, contradiction_score / total_evidence)
    
    return support_score, contradiction_score

def calculate_verdict(confidence: float, support_score: float, contradiction_score: float) -> str:
    """Determine the verdict based on confidence and evidence scores"""
    if confidence >= 0.7:
        if support_score > contradiction_score:
            return "True"
        else:
            return "False"
    elif confidence >= 0.4:
        return "Partially Verified"
    elif confidence >= 0.2:
        return "Unclear"
    else:
        return "Unverifiable"

async def search_evidence(claim: str, api_key: str) -> List[Dict[str, Any]]:
    """
    Search for evidence using Serper API.
    
    Args:
        claim (str): The claim to search for
        api_key (str): Serper API key
        
    Returns:
        List[Dict[str, Any]]: List of evidence items
    """
    try:
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": claim,
            "gl": "us",
            "hl": "en",
            "num": 5
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    evidence = []
                    
                    # Extract organic results
                    if "organic" in data:
                        for result in data["organic"]:
                            evidence.append({
                                "title": result.get("title", ""),
                                "snippet": result.get("snippet", ""),
                                "source": result.get("link", ""),
                                "position": result.get("position", 0)
                            })
                    
                    return evidence
                else:
                    logger.error(f"Serper API error: {response.status}")
                    return []
                    
    except Exception as e:
        logger.error(f"Error searching evidence: {str(e)}")
        return []

async def analyze_with_gemini(claim: str, evidence: List[Dict]) -> Dict:
    """Analyze claim using Gemini API as fallback"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        
        # Prepare evidence context
        evidence_text = "\n".join([
            f"Source: {e['source']}\nSnippet: {e['snippet']}\n"
            for e in evidence[:3]  # Use top 3 pieces of evidence
        ])
        
        prompt = f"""
        Analyze this claim and determine if it's true, false, or unverifiable based on the evidence:
        
        Claim: {claim}
        
        Evidence:
        {evidence_text}
        
        Provide your analysis in JSON format:
        {{
            "verdict": "True/False/Unverifiable",
            "confidence": 0.0-1.0,
            "explanation": "Brief explanation",
            "limitations": "Any limitations in the analysis"
        }}
        """
        
        response = await model.generate_content(prompt)
        result = json.loads(response.text)
        return result
    except Exception as e:
        logger.error(f"Error with Gemini API: {str(e)}")
        return None

async def run_proof_agent(claim: str, serper_api_key: str) -> dict:
    """
    Verify a claim using evidence and Gemini.
    
    Args:
        claim (str): The claim to verify
        serper_api_key (str): Serper API key for evidence search
        
    Returns:
        dict: Verification results including confidence and evidence
    """
    try:
        # Initialize Gemini
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        
        # Search for evidence
        evidence = await search_evidence(claim, serper_api_key)
        
        # Create prompt with evidence
        evidence_text = "\n".join([
            f"Source {i+1}: {e['title']}\n{e['snippet']}\nURL: {e['source']}\n"
            for i, e in enumerate(evidence)
        ])
        
        prompt = f"""
        Verify the following claim using the provided evidence:
        
        Claim: {claim}
        
        Evidence:
        {evidence_text}
        
        Please provide:
        1. A verdict (VERIFIED, PARTIALLY_VERIFIED, or UNVERIFIED)
        2. A confidence score (0-1)
        3. A detailed explanation
        4. Key evidence points
        
        Format the response as a JSON object with the following structure:
        {{
            "verdict": str,
            "confidence": float,
            "explanation": str,
            "evidence": [
                {{
                    "title": str,
                    "snippet": str,
                    "source": str,
                    "relevance": float
                }}
            ],
            "timestamp": str
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
                "verdict": "UNVERIFIED",
                "confidence": 0.0,
                "explanation": "Error parsing response",
                "evidence": [],
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error in proof agent: {str(e)}")
        return {
            "verdict": "UNVERIFIED",
            "confidence": 0.0,
            "explanation": str(e),
            "evidence": [],
            "timestamp": datetime.now().isoformat()
        }

# For testing
if __name__ == "__main__":
    test_claims = """The Earth is an oblate spheroid
The Earth is flat
Aliens created the pyramids"""
    
    # Run test
    try:
        result = asyncio.run(run_proof_agent(test_claims))
        print("\nFinal Results:")
        print(json.dumps(result, indent=2))
    except ValueError as e:
        print(f"Error: {str(e)}")
        print("\nPlease make sure you have set the SERPER_API_KEY in your .env file:")
        print("SERPER_API_KEY=your_api_key_here")
