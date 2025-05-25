import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from PIL import Image, ImageStat
import exifread
import google.generativeai as genai
from dotenv import load_dotenv
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class MediaScanAgent:
    """Agent for analyzing images using metadata, forensics, and AI-powered analysis."""
    
    def __init__(self):
        """Initialize the MediaScan agent with API configurations."""
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.search_api_key = os.getenv("SEARCH_API_KEY")
        
        # Configure Gemini
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        else:
            self.model = None
            logger.warning("Gemini API key not found. AI analysis will be limited.")
        
    async def analyze_media(self, media_path: str) -> Dict:
        """
        Analyze image for potential manipulation or AI generation.
        
        Args:
            media_path: Path to the image file
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Basic file validation
            if not os.path.exists(media_path):
                raise FileNotFoundError(f"Image file not found: {media_path}")
            
            # Extract metadata and image properties
            metadata = await self._extract_metadata(media_path)
            image_properties = await self._analyze_image_properties(media_path)
            
            # Perform image forensics analysis
            forensics = await self._perform_forensics_analysis(media_path)
            
            # Perform reverse image search
            search_results = await self._reverse_image_search(media_path)
            
            # Perform AI analysis
            ai_analysis = await self._analyze_with_ai(
                media_path, 
                metadata, 
                image_properties,
                forensics,
                search_results
            )
            
            # Combine results
            result = {
                "timestamp": datetime.now().isoformat(),
                "file_path": media_path,
                "metadata": metadata,
                "image_properties": image_properties,
                "forensics_analysis": forensics,
                "search_results": search_results,
                "ai_analysis": ai_analysis,
                "verdict": self._determine_verdict(ai_analysis),
                "confidence_score": ai_analysis.get("confidence", 0.0),
                "reasoning": ai_analysis.get("reasoning", "")
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing media: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def _extract_metadata(self, media_path: str) -> Dict:
        """Extract and analyze metadata from image file."""
        metadata = {
            "file_size": os.path.getsize(media_path),
            "creation_date": None,
            "modification_date": None,
            "exif_data": {},
            "anomalies": []
        }
        
        try:
            # Get basic file dates
            metadata["creation_date"] = datetime.fromtimestamp(
                os.path.getctime(media_path)
            ).isoformat()
            metadata["modification_date"] = datetime.fromtimestamp(
                os.path.getmtime(media_path)
            ).isoformat()
            
            # Extract EXIF data
            with open(media_path, 'rb') as f:
                exif = exifread.process_file(f)
                metadata["exif_data"] = {
                    str(tag): str(value)
                    for tag, value in exif.items()
                }
            
            # Check for metadata anomalies
            metadata["anomalies"] = self._check_metadata_anomalies(metadata)
                    
        except Exception as e:
            logger.warning(f"Error extracting metadata: {str(e)}")
            
        return metadata
    
    def _check_metadata_anomalies(self, metadata: Dict) -> List[str]:
        """Check for suspicious patterns in metadata."""
        anomalies = []
        
        # Check creation vs modification dates
        if metadata["creation_date"] and metadata["modification_date"]:
            creation = datetime.fromisoformat(metadata["creation_date"])
            modification = datetime.fromisoformat(metadata["modification_date"])
            if modification < creation:
                anomalies.append("Modification date is earlier than creation date")
        
        # Check EXIF data
        exif = metadata["exif_data"]
        if "EXIF DateTimeOriginal" in exif and "EXIF DateTimeDigitized" in exif:
            if exif["EXIF DateTimeOriginal"] != exif["EXIF DateTimeDigitized"]:
                anomalies.append("Original and digitized dates don't match")
        
        # Check for missing critical EXIF data
        critical_tags = ["EXIF DateTimeOriginal", "EXIF Make", "EXIF Model"]
        missing_tags = [tag for tag in critical_tags if tag not in exif]
        if missing_tags:
            anomalies.append(f"Missing critical EXIF data: {', '.join(missing_tags)}")
        
        return anomalies
    
    async def _analyze_image_properties(self, media_path: str) -> Dict:
        """Analyze basic image properties and quality metrics."""
        try:
            with Image.open(media_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate image statistics
                stat = ImageStat.Stat(img)
                
                # Get basic properties
                properties = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height,
                    "dpi": img.info.get('dpi', None),
                    "compression": img.info.get('compression', None),
                    "quality_metrics": {
                        "brightness": stat.mean[0],
                        "contrast": stat.stddev[0],
                        "color_balance": {
                            "red": stat.mean[0],
                            "green": stat.mean[1],
                            "blue": stat.mean[2]
                        }
                    }
                }
                
                # Add aspect ratio
                properties["aspect_ratio"] = round(img.width / img.height, 2)
                
                # Check for common image dimensions
                properties["is_standard_resolution"] = self._is_standard_resolution(img.width, img.height)
                
                return properties
                
        except Exception as e:
            logger.warning(f"Error analyzing image properties: {str(e)}")
            return {}
    
    def _is_standard_resolution(self, width: int, height: int) -> bool:
        """Check if image dimensions match common standard resolutions."""
        common_resolutions = [
            (1920, 1080),  # Full HD
            (1280, 720),   # HD
            (3840, 2160),  # 4K
            (2560, 1440),  # 2K
            (800, 600),    # SVGA
            (1024, 768),   # XGA
        ]
        return (width, height) in common_resolutions
    
    async def _perform_forensics_analysis(self, media_path: str) -> Dict:
        """Perform basic image forensics analysis."""
        try:
            with Image.open(media_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Convert to numpy array for analysis
                img_array = np.array(img)
                
                # Basic forensics checks
                forensics = {
                    "error_level_analysis": self._error_level_analysis(img_array),
                    "noise_analysis": self._analyze_noise(img_array),
                    "compression_artifacts": self._check_compression_artifacts(img_array),
                    "color_consistency": self._check_color_consistency(img_array)
                }
                
                return forensics
                
        except Exception as e:
            logger.warning(f"Error in forensics analysis: {str(e)}")
            return {}
    
    def _error_level_analysis(self, img_array: np.ndarray) -> Dict:
        """Perform Error Level Analysis (ELA) to detect edited regions."""
        # TODO: Implement proper ELA
        return {
            "score": 0.0,
            "suspicious_regions": []
        }
    
    def _analyze_noise(self, img_array: np.ndarray) -> Dict:
        """Analyze image noise patterns."""
        # TODO: Implement noise analysis
        return {
            "noise_level": 0.0,
            "noise_pattern": "unknown"
        }
    
    def _check_compression_artifacts(self, img_array: np.ndarray) -> Dict:
        """Check for compression artifacts."""
        # TODO: Implement compression artifact detection
        return {
            "has_artifacts": False,
            "artifact_score": 0.0
        }
    
    def _check_color_consistency(self, img_array: np.ndarray) -> Dict:
        """Check color consistency across the image."""
        # TODO: Implement color consistency analysis
        return {
            "is_consistent": True,
            "inconsistency_score": 0.0
        }
    
    async def _reverse_image_search(self, media_path: str) -> Dict:
        """
        Perform reverse image search using external API.
        This is a placeholder for actual API integration.
        """
        # TODO: Implement actual reverse image search API integration
        return {
            "matches": [],
            "sources": [],
            "confidence": 0.0
        }
    
    async def _analyze_with_ai(self, media_path: str, metadata: Dict, 
                             image_properties: Dict, forensics: Dict, 
                             search_results: Dict) -> Dict:
        """Analyze image using Gemini API with enhanced prompt engineering."""
        try:
            if not self.model:
                return {
                    "confidence": 0.0,
                    "reasoning": "AI analysis requires Gemini API key",
                    "details": {}
                }
            
            # Create detailed prompt for Gemini
            prompt = f"""
            Analyze this image for potential manipulation or AI generation. Consider the following aspects:

            1. Metadata Analysis:
            - Creation Date: {metadata.get('creation_date')}
            - File Size: {metadata.get('file_size')} bytes
            - Metadata Anomalies: {metadata.get('anomalies', [])}
            - EXIF Data: {json.dumps(metadata.get('exif_data', {}), indent=2)}

            2. Image Properties:
            - Resolution: {image_properties.get('width')}x{image_properties.get('height')}
            - Format: {image_properties.get('format')}
            - Aspect Ratio: {image_properties.get('aspect_ratio')}
            - Quality Metrics: {json.dumps(image_properties.get('quality_metrics', {}), indent=2)}

            3. Forensics Analysis:
            - Error Level Analysis: {json.dumps(forensics.get('error_level_analysis', {}), indent=2)}
            - Noise Analysis: {json.dumps(forensics.get('noise_analysis', {}), indent=2)}
            - Compression Artifacts: {json.dumps(forensics.get('compression_artifacts', {}), indent=2)}
            - Color Consistency: {json.dumps(forensics.get('color_consistency', {}), indent=2)}

            4. Search Results:
            {json.dumps(search_results, indent=2)}

            Please provide a detailed analysis addressing:
            1. Are there any suspicious patterns in the metadata or image properties?
            2. Does the forensics analysis reveal any signs of manipulation?
            3. Does the image appear to be AI-generated? If so, what are the indicators?
            4. What is your confidence level in this assessment (0-1)?
            5. What specific evidence supports your conclusion?

            Format your response as a structured analysis with clear sections and confidence scores.
            """
            
            # Get AI analysis
            response = await self.model.generate_content(prompt)
            analysis = response.text
            
            # Parse the response and structure it
            return {
                "confidence": 0.0,  # TODO: Extract confidence from response
                "reasoning": analysis,
                "details": {
                    "metadata_analysis": "TODO",
                    "forensics_analysis": "TODO",
                    "manipulation_indicators": "TODO",
                    "ai_generation_indicators": "TODO"
                }
            }
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return {
                "confidence": 0.0,
                "reasoning": f"Error in AI analysis: {str(e)}",
                "details": {}
            }
    
    def _determine_verdict(self, analysis: Dict) -> str:
        """Determine the final verdict based on analysis results."""
        confidence = analysis.get("confidence", 0.0)
        
        if confidence >= 0.85:
            return "AI-Generated"
        elif confidence >= 0.5:
            return "Manipulated"
        else:
            return "Authentic"

async def main():
    """Example usage of the MediaScan agent."""
    agent = MediaScanAgent()
    result = await agent.analyze_media("path/to/image.jpg")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 