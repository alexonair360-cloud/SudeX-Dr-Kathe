import requests
import json

# Fetch voices.json from Bhashini
response = requests.get("https://app.bhashini.ai/voices.json")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    voices = response.json()
    
    # Save to file
    with open("voices.json", "w", encoding="utf-8") as f:
        json.dump(voices, f, indent=2, ensure_ascii=False)
    
    print("Voices data saved to voices.json")
    
    # Print structure
    print("\nVoices structure:")
    print(json.dumps(voices, indent=2, ensure_ascii=False)[:2000])
else:
    print(f"Failed to fetch voices: {response.text}")
