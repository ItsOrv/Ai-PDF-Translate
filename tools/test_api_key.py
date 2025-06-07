"""
Test Gemini API key validity.
"""
import os
import json
import requests
from dotenv import load_dotenv

def test_api_key_direct():
    """
    Test API key directly via HTTP request.
    
    Returns:
        bool: True if API key is valid, False otherwise
    """
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment variables
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("No API key found. Please set GEMINI_API_KEY in .env file")
        return False
    
    print(f"Using API key: {api_key[:4]}...")  # Only show first 4 chars for security
    
    # Test endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    # Simple prompt for testing
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Hello, testing API key validity. Please respond with 'API key is valid' if you receive this."
                    }
                ]
            }
        ]
    }
    
    # Make the request
    try:
        response = requests.post(url, json=data)
        
        # Check response
        if response.status_code == 200:
            print("✅ API key is valid!")
            return True
        else:
            print(f"❌ API key is invalid. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing API key: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_api_key_direct()
    if not success:
        print("\nPlease check your API key and try again.")
    exit(0 if success else 1) 