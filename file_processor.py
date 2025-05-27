import PyPDF2
import nltk
from typing import List, Dict, Any
import re
from config import Config

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class FileProcessor:
    def __init__(self):
        self.claim_keywords = {
            'assertion': ['claim', 'assert', 'state', 'declare', 'allege'],
            'fact': ['fact', 'true', 'real', 'actual', 'confirmed'],
            'opinion': ['think', 'believe', 'feel', 'consider', 'view'],
            'evidence': ['prove', 'show', 'demonstrate', 'verify', 'confirm']
        }
    
    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(file_content)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise ValueError(f"Error processing PDF: {str(e)}")
    
    def extract_text_from_txt(self, file_content: bytes) -> str:
        """Extract text from TXT file"""
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return file_content.decode('latin-1')
            except Exception as e:
                raise ValueError(f"Error processing text file: {str(e)}")
    
    def extract_claims(self, text: str) -> List[Dict[str, Any]]:
        """Extract potential claims from text using NLP"""
        # Split text into sentences
        sentences = nltk.sent_tokenize(text)
        claims = []
        
        for sentence in sentences:
            # Skip very short sentences
            if len(sentence.split()) < 3:
                continue
            
            # Check if sentence contains claim-related keywords
            if self._is_potential_claim(sentence):
                # Extract subject, predicate, and object
                subject, predicate, object_text = self._extract_claim_components(sentence)
                
                if subject and predicate and object_text:
                    claims.append({
                        "claim_text": sentence.strip(),
                        "subject": subject.strip(),
                        "predicate": predicate.strip(),
                        "object": object_text.strip(),
                        "confidence": self._calculate_claim_confidence(sentence)
                    })
        
        return claims
    
    def _is_potential_claim(self, sentence: str) -> bool:
        """Check if a sentence is likely to contain a claim"""
        sentence_lower = sentence.lower()
        
        # Check for claim-related keywords
        for category, keywords in self.claim_keywords.items():
            if any(keyword in sentence_lower for keyword in keywords):
                return True
        
        # Check for common claim patterns
        claim_patterns = [
            r'\b(is|are|was|were)\b',
            r'\b(has|have|had)\b',
            r'\b(can|could|will|would|should)\b',
            r'\b(proves?|shows?|demonstrates?)\b'
        ]
        
        return any(re.search(pattern, sentence_lower) for pattern in claim_patterns)
    
    def _extract_claim_components(self, sentence: str) -> tuple:
        """Extract subject, predicate, and object from a sentence"""
        # Basic pattern matching for now - could be improved with more sophisticated NLP
        words = sentence.split()
        
        # Find the main verb (predicate)
        verb_index = -1
        for i, word in enumerate(words):
            if word.lower() in ['is', 'are', 'was', 'were', 'has', 'have', 'had']:
                verb_index = i
                break
        
        if verb_index == -1:
            return None, None, None
        
        subject = ' '.join(words[:verb_index])
        predicate = words[verb_index]
        object_text = ' '.join(words[verb_index + 1:])
        
        return subject, predicate, object_text
    
    def _calculate_claim_confidence(self, sentence: str) -> float:
        """Calculate initial confidence score for a potential claim"""
        confidence = 0.5  # Base confidence
        
        # Adjust confidence based on sentence length
        words = sentence.split()
        if 5 <= len(words) <= 20:
            confidence += 0.1
        
        # Adjust confidence based on presence of claim keywords
        sentence_lower = sentence.lower()
        for category, keywords in self.claim_keywords.items():
            if any(keyword in sentence_lower for keyword in keywords):
                confidence += 0.1
                break
        
        # Adjust confidence based on presence of evidence indicators
        evidence_indicators = ['because', 'since', 'due to', 'as shown by', 'according to']
        if any(indicator in sentence_lower for indicator in evidence_indicators):
            confidence += 0.1
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    def process_file(self, file_content: bytes, file_extension: str) -> List[Dict[str, Any]]:
        """Process uploaded file and extract claims"""
        if file_extension not in Config.ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        # Extract text based on file type
        if file_extension == '.pdf':
            text = self.extract_text_from_pdf(file_content)
        else:  # .txt
            text = self.extract_text_from_txt(file_content)
        
        # Extract claims from text
        return self.extract_claims(text) 