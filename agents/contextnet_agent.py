import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import aiohttp
from dotenv import load_dotenv
import google.generativeai as genai
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class BiasDirection(Enum):
    """Enum for political/ideological bias directions."""
    LEFT = "Left"
    CENTER = "Center"
    RIGHT = "Right"
    MIXED = "Mixed"
    UNKNOWN = "Unknown"

@dataclass
class SearchResult:
    """Data class for search results."""
    title: str
    snippet: str
    url: str
    source: str
    date: Optional[str] = None

class ContextNetAgent:
    """Agent for providing context and bias analysis on claims or topics."""
    
    def __init__(self):
        """Initialize the ContextNet agent with API configurations."""
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.search_api_key = os.getenv("SEARCH_API_KEY")
        self.search_engine = os.getenv("SEARCH_ENGINE", "brave")  # brave, serpapi, bing
        
        # Configure Gemini
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        else:
            self.model = None
            logger.warning("Gemini API key not found. Analysis will be limited.")
    
    async def analyze_context(self, claim: str) -> Dict:
        """
        Analyze a claim or topic for context and bias.
        
        Args:
            claim: The claim or topic to analyze
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Perform parallel analysis
            search_task = self._search_related_content(claim)
            entities_task = self._extract_entities(claim)
            
            # Wait for search and entity extraction
            search_results, entities = await asyncio.gather(
                search_task,
                entities_task
            )
            
            # Perform AI analysis on the collected data
            analysis = await self._analyze_with_ai(claim, search_results, entities)
            
            # Combine results
            result = {
                "timestamp": datetime.now().isoformat(),
                "claim": claim,
                "background": analysis.get("background", ""),
                "bias": analysis.get("bias", BiasDirection.UNKNOWN.value),
                "confidence_bias": analysis.get("confidence_bias", 0.0),
                "keywords": analysis.get("keywords", []),
                "entities": entities,
                "controversial_aspects": analysis.get("controversial_aspects", []),
                "sources": [result.url for result in search_results],
                "confidence_scores": {
                    "background": analysis.get("confidence_background", 0.0),
                    "bias": analysis.get("confidence_bias", 0.0),
                    "keywords": analysis.get("confidence_keywords", 0.0)
                },
                "explanation": (
                    f"Bias assessment is based on analysis of related articles and identified entities. "
                    f"Confidence ({analysis.get('confidence_bias', 0.0):.2f}) reflects the clarity and agreement among sources. "
                    f"Background and controversial aspects are summarized from the most relevant content."
                )
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing context: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def _search_related_content(self, claim: str) -> List[SearchResult]:
        """Search for related content using the configured search engine."""
        try:
            if not self.search_api_key:
                logger.warning("Search API key not found. Using mock data.")
                return self._get_mock_search_results(claim)
            
            # TODO: Implement actual search API integration
            # This is a placeholder for the actual search implementation
            return self._get_mock_search_results(claim)
            
        except Exception as e:
            logger.error(f"Error in search: {str(e)}")
            return []
    
    def _get_mock_search_results(self, claim: str) -> List[SearchResult]:
        """Generate mock search results for testing."""
        return [
            SearchResult(
                title="Example Article 1",
                snippet="This is a sample article about the topic.",
                url="https://example.com/1",
                source="Example News",
                date="2024-03-20"
            ),
            SearchResult(
                title="Example Article 2",
                snippet="Another perspective on the subject.",
                url="https://example.com/2",
                source="Sample Media",
                date="2024-03-19"
            )
        ]
    
    async def _extract_entities(self, claim: str) -> List[Dict]:
        """Extract named entities from the claim."""
        try:
            if not self.model:
                return []
            
            prompt = f"""
            Extract key entities from this claim. For each entity, provide:
            1. The entity name
            2. The entity type (person, organization, location, etc.)
            3. The entity's role or significance in the claim
            
            Claim: {claim}
            
            Format the response as a JSON list of objects with 'name', 'type', and 'role' fields.
            """
            
            response = await self.model.generate_content(prompt)
            # TODO: Parse response and extract entities
            return []
            
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return []
    
    async def _analyze_with_ai(self, claim: str, search_results: List[SearchResult], 
                             entities: List[Dict]) -> Dict:
        """Analyze the claim and search results using Gemini API."""
        try:
            if not self.model:
                return {
                    "background": "AI analysis requires Gemini API key",
                    "bias": BiasDirection.UNKNOWN.value,
                    "confidence_bias": 0.0,
                    "keywords": [],
                    "controversial_aspects": []
                }
            
            # Prepare search results for analysis
            search_context = "\n".join([
                f"Title: {result.title}\nSnippet: {result.snippet}\nSource: {result.source}\n"
                for result in search_results
            ])
            
            # Create detailed prompt for Gemini
            prompt = f"""
            Analyze this claim and related content for context and bias.

            Claim: {claim}

            Related Content:
            {search_context}

            Entities Identified:
            {json.dumps(entities, indent=2)}

            Please provide a comprehensive analysis including:

            1. A neutral, factual background summary of the topic
            2. Political/ideological bias assessment (Left, Center, Right, or Mixed)
            3. Key keywords and phrases
            4. Potentially controversial aspects
            5. Confidence scores for each assessment (0-1)

            Format your response as a structured JSON object with the following fields:
            - background: string
            - bias: string (Left/Center/Right/Mixed)
            - confidence_bias: number (0-1)
            - keywords: string[]
            - controversial_aspects: string[]
            - confidence_background: number (0-1)
            - confidence_keywords: number (0-1)
            """
            
            # Get AI analysis
            response = await self.model.generate_content(prompt)
            
            try:
                # Parse the response as JSON
                analysis = json.loads(response.text)
                return analysis
            except json.JSONDecodeError:
                logger.error("Failed to parse AI response as JSON")
                return {
                    "background": response.text,
                    "bias": BiasDirection.UNKNOWN.value,
                    "confidence_bias": 0.0,
                    "keywords": [],
                    "controversial_aspects": []
                }
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return {
                "background": f"Error in analysis: {str(e)}",
                "bias": BiasDirection.UNKNOWN.value,
                "confidence_bias": 0.0,
                "keywords": [],
                "controversial_aspects": []
            }

async def main():
    """Example usage of the ContextNet agent."""
    agent = ContextNetAgent()
    result = await agent.analyze_context(
        "The government's new climate policy will increase energy costs by 30%"
    )
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 