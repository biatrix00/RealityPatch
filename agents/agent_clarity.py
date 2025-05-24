import google.generativeai as genai

def run_clarity_agent(text, model, ask_path="ask_files/clarity.ask"):
    # Read the prompt template
    with open(ask_path, "r") as file:
        prompt_template = file.read()

    # Construct the full prompt
    full_prompt = f"{prompt_template}\n\nINPUT:\n{text.strip()}"
    
    # Generate response using the provided model instance
    response = model.generate_content(full_prompt)
    
    return response.text.strip()