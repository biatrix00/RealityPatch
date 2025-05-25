import os
import sys
import logging
import google.generativeai as genai
from dotenv import load_dotenv
import os.path

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
INPUT_FILE = os.getenv("INPUT_FILE", "data/test_inputs.txt")

# Configure the Gemini API
try:
    genai.configure(api_key=API_KEY)
    MODEL_NAME = "models/gemini-1.5-flash-latest"  # Gemini Flash free trial model
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {str(e)}")
    sys.exit(1)

def load_input(input_path=INPUT_FILE):
    """Load input text from a file."""
    try:
        with open(input_path, "r", encoding='utf-8') as f:
            text = f.read()
            if not text.strip():
                logger.error(f"Input file '{input_path}' is empty.")
                return ""
            return text
    except FileNotFoundError:
        logger.error(f"Input file not found at {input_path}")
        return ""
    except Exception as e:
        logger.error(f"Error reading input file: {str(e)}")
        return ""

def run_clarity_agent(text, model, ask_path=None):
    """Run the clarity agent to extract claims from text using the provided model."""
    if ask_path is None:
        ask_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ask_files", "clarity.ask")
    try:
        with open(ask_path, "r", encoding='utf-8') as file:
            prompt_template = file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt template not found at {ask_path}")
    except Exception as e:
        raise Exception(f"Error reading prompt template: {str(e)}")
    full_prompt = f"{prompt_template}\n\nINPUT:\n{text.strip()}"
    try:
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error from Gemini API: {str(e)}")
        return None

def main():
    """Main entry point for the script."""
    text = load_input()
    if not API_KEY:
        logger.error("GEMINI_API_KEY environment variable not set")
        sys.exit(1)
    elif not text:
        logger.error("No input text to process")
        sys.exit(1)
    else:
        try:
            logger.info(f"Initializing model {MODEL_NAME}")
            model = genai.GenerativeModel(MODEL_NAME)
            logger.info("Processing input text")
            result = run_clarity_agent(text, model)
            print("\n--- Claims Detected ---\n")
            if result and any(char.isalnum() for char in result):
                print(result)
            else:
                print("No claims detected or an error occurred.")
        except Exception as e:
            logger.error(f"Error during processing: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main()
            