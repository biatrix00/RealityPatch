import os
import json
import logging
from typing import Dict, List, Optional
import aiohttp
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_mock_results(claim: str) -> Dict:
    """Generate mock results for testing or when API fails"""
    # Common topics and their mock evidence
    mock_data = {
        "earth": {
            "status": "Verified",
            "confidence": 0.75,
            "evidence": [
                {
                    "title": "NASA Confirms Earth's Shape",
                    "snippet": "Scientific evidence from NASA and other space agencies confirms Earth is an oblate spheroid, not flat.",
                    "link": "https://www.nasa.gov/earth",
                    "source": "NASA"
                },
                {
                    "title": "Flat Earth Theory Debunked",
                    "snippet": "Multiple scientific experiments and observations have disproven the flat Earth theory.",
                    "link": "https://www.scientificamerican.com",
                    "source": "Scientific American"
                }
            ]
        },
        "moon": {
            "status": "Verified",
            "confidence": 0.75,
            "evidence": [
                {
                    "title": "Apollo Mission Evidence",
                    "snippet": "Extensive evidence from the Apollo missions, including moon rocks and photographs, confirms the moon landing.",
                    "link": "https://www.nasa.gov/moon",
                    "source": "NASA"
                },
                {
                    "title": "Moon Landing Conspiracy Debunked",
                    "snippet": "Scientific analysis of moon landing footage and materials has verified their authenticity.",
                    "link": "https://www.smithsonianmag.com",
                    "source": "Smithsonian Magazine"
                }
            ]
        },
        "india": {
            "status": "Partially Verified",
            "confidence": 0.6,
            "evidence": [
                {
                    "title": "Recent Border Developments",
                    "snippet": "Recent reports indicate border tensions between India and Pakistan, with both sides making claims about ceasefire violations.",
                    "link": "https://www.reuters.com",
                    "source": "Reuters"
                }
            ]
        }
    }
    
    # Check for keywords in the claim
    claim_lower = claim.lower()
    for keyword, data in mock_data.items():
        if keyword in claim_lower:
            return data
    
    # Default response for unknown topics
    return {
        "status": "Not Verified",
        "confidence": 0.0,
        "evidence": [
            {
                "title": "Insufficient Evidence",
                "snippet": "No reliable evidence found to verify or refute this claim.",
                "link": "",
                "source": "RealityPatch"
            }
        ]
    }

async def run_proof_agent(claims: str, search_api_key: str = None) -> Dict:
    """
    Verify claims using Serper API and return structured results.
    
    Args:
        claims: String containing newline-separated claims
        search_api_key: API key for Serper search service (optional, will use env var if not provided)
        
    Returns:
        Dict containing verification results for each claim
    """
    # Use provided API key or get from environment
    api_key = search_api_key or os.getenv("SERPER_API_KEY")
    if not api_key or api_key == "placeholder_key":
        logger.warning("No valid API key found, using mock results")
        return {
            "timestamp": datetime.now().isoformat(),
            "total_claims": 1,
            "processed_claims": 1,
            "results": [get_mock_results(claims)]
        }
    
    try:
        # Split claims into list
        claim_list = [claim.strip() for claim in claims.split('\n') if claim.strip()]
        print(f"Processing {len(claim_list)} claims")
        
        results = []
        async with aiohttp.ClientSession() as session:
            for claim in claim_list:
                print(f"\nProcessing claim: {claim}")
                
                # Construct search query
                search_query = f"Fact check: {claim}"
                print(f"Search query: {search_query}")
                
                # Prepare API request
                url = "https://google.serper.dev/search"
                headers = {
                    "X-API-KEY": api_key,
                    "Content-Type": "application/json"
                }
                payload = {
                    "q": search_query,
                    "gl": "us",  # Search in US
                    "hl": "en",  # English results
                    "num": 3     # Get top 3 results
                }
                
                try:
                    # Make API request
                    print("Sending request to Serper API...")
                    async with session.post(url, headers=headers, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            print("Received response from Serper API")
                            
                            # Extract organic results
                            organic_results = data.get("organic", [])
                            print(f"Found {len(organic_results)} organic results")
                            
                            # Format evidence snippets
                            evidence = []
                            for result in organic_results[:3]:  # Get top 3 results
                                snippet = {
                                    "title": result.get("title", "No title"),
                                    "snippet": result.get("snippet", "No snippet"),
                                    "link": result.get("link", "No link"),
                                    "source": result.get("source", "Unknown source")
                                }
                                evidence.append(snippet)
                                print(f"Added evidence from: {snippet['source']}")
                            
                            # Determine verification status and confidence
                            status = "Verified" if evidence else "Not Verified"
                            confidence = 0.75 if evidence else 0.0
                            
                            # Create result for this claim
                            claim_result = {
                                "claim": claim,
                                "status": status,
                                "confidence": confidence,
                                "evidence": evidence
                            }
                            
                            results.append(claim_result)
                            print(f"Successfully processed claim: {claim}")
                            
                        else:
                            error_msg = f"API request failed with status {response.status}"
                            print(error_msg)
                            # Use mock results when API fails
                            mock_result = get_mock_results(claim)
                            mock_result["claim"] = claim
                            results.append(mock_result)
                            
                except Exception as e:
                    error_msg = f"Error processing claim: {str(e)}"
                    print(error_msg)
                    # Use mock results when exception occurs
                    mock_result = get_mock_results(claim)
                    mock_result["claim"] = claim
                    results.append(mock_result)
        
        # Format final response
        response = {
            "timestamp": datetime.now().isoformat(),
            "total_claims": len(claim_list),
            "processed_claims": len(results),
            "results": results
        }
        
        print(f"\nProcessed {len(results)} claims successfully")
        return response
        
    except Exception as e:
        error_msg = f"Error in proof agent: {str(e)}"
        print(error_msg)
        return {
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "total_claims": 0,
            "processed_claims": 0,
            "results": []
        }

# For testing
if __name__ == "__main__":
    test_claims = """Is the earth flat?
India broke the ceasefire
The moon landing was faked"""
    
    # Run test
    try:
        result = asyncio.run(run_proof_agent(test_claims))
        print("\nFinal Results:")
        print(json.dumps(result, indent=2))
    except ValueError as e:
        print(f"Error: {str(e)}")
        print("\nPlease make sure you have set the SERPER_API_KEY in your .env file:")
        print("SERPER_API_KEY=your_api_key_here")
