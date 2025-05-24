import os
import google.generativeai as genai
from dotenv import load_dotenv
from agents.agent_clarity import run_clarity_agent

load_dotenv()  # Load environment variables from .env file
API_KEY = os.getenv("GEMINI_API_KEY")

# Configure the Gemini API
genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-2.0-flash"

def load_input():
    try:
        with open("data/test_inputs.txt", "r") as f:
            return f.read()
    except FileNotFoundError:
        print("Input file not found.")
        return ""

if __name__ == "__main__":
    text = load_input()
    if not API_KEY:
        print("Error: GEMINI_API_KEY environment variable not set.")
    elif not text:
        print("No input text to process.")
    else:
        try:
            model = genai.GenerativeModel(MODEL_NAME)
            result = run_clarity_agent(text, model)
            print("\n--- Claims Detected ---\n")
            print(result)
        except Exception as e:
            print(f"Error during processing: {str(e)}")