import os
import json
import requests

def test_translation():
    """Test the Portuguese-English translation using the Groq API."""
    print("Testing Portuguese-English Translation")
    print("--------------------------------------")
    
    # Load configuration
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error: Could not load config.json")
        return
    
    # Get API key
    api_key = config["api"]["api_key"]
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("Error: Please set your API key in config.json")
        return
    
    # Test phrases
    test_phrases = [
        {"text": "Olá, como vai você?", "source": "pt", "target": "en", "description": "Portuguese to English"},
        {"text": "Hello, how are you?", "source": "en", "target": "pt", "description": "English to Portuguese"},
        {"text": "Eu gostaria de traduzir esta mensagem para inglês.", "source": "auto", "target": "en", "description": "Auto-detect to English"},
        {"text": "I would like to translate this message to Portuguese.", "source": "auto", "target": "pt", "description": "Auto-detect to Portuguese"}
    ]
    
    # Test each phrase
    for phrase in test_phrases:
        print(f"\nTesting: {phrase['description']}")
        print(f"Original: {phrase['text']}")
        
        # Prepare the prompt for translation
        if phrase['source'] == "auto" and phrase['target'] == "pt":
            prompt = f"Translate the following text to Portuguese (Brazil). Maintain the original tone and meaning:\n\n{phrase['text']}"
        elif phrase['source'] == "auto" and phrase['target'] == "en":
            prompt = f"Translate the following text to English. Maintain the original tone and meaning:\n\n{phrase['text']}"
        elif phrase['source'] == "pt" and phrase['target'] == "en":
            prompt = f"Translate the following Portuguese text to English. Maintain the original tone and meaning:\n\n{phrase['text']}"
        elif phrase['source'] == "en" and phrase['target'] == "pt":
            prompt = f"Translate the following English text to Portuguese (Brazil). Maintain the original tone and meaning:\n\n{phrase['text']}"
        else:
            prompt = f"Translate the following text from {phrase['source']} to {phrase['target']}. Maintain the original tone and meaning:\n\n{phrase['text']}"
        
        # Prepare API request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": config["api"]["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1024
        }
        
        try:
            # Make API request
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result["choices"][0]["message"]["content"].strip()
                print(f"Translated: {translated_text}")
            else:
                print(f"API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_translation() 