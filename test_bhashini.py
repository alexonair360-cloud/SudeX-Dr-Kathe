import requests
import json

# Test Bhashini API directly
API_KEY = "a6071d99282a4e839841b0affe312e6c"
ENDPOINT = "https://tts.bhashini.ai/v1/synthesize"

# Test with Hindi
payload_hindi = {
    "text": "नमस्ते, यह एक परीक्षण है",
    "language": "Hindi",
    "voiceName": "hi-f1",
    "voiceStyle": "Neutral",
    "speechRate": 1.0
}

# Test with Kannada
payload_kannada = {
    "text": "ನಮಸ್ಕಾರ, ಇದು ಪರೀಕ್ಷೆ",
    "language": "Kannada", 
    "voiceName": "kn-f1",
    "voiceStyle": "Neutral",
    "speechRate": 1.0
}

headers = {
    "Content-Type": "application/json",
    "X-API-KEY": API_KEY
}

results = []

results.append("=" * 60)
results.append("Testing Hindi...")
results.append("=" * 60)
response_hindi = requests.post(ENDPOINT, headers=headers, json=payload_hindi)
results.append(f"Status: {response_hindi.status_code}")
if response_hindi.status_code == 200:
    results.append(f"SUCCESS! Audio length: {len(response_hindi.content)} bytes")
    # Save audio
    with open("test_hindi.mp3", "wb") as f:
        f.write(response_hindi.content)
    results.append("Saved to test_hindi.mp3")
else:
    results.append(f"ERROR Response Text: {response_hindi.text}")
    try:
        error_json = response_hindi.json()
        results.append(f"ERROR JSON: {json.dumps(error_json, indent=2)}")
    except:
        pass

results.append("\n" + "=" * 60)
results.append("Testing Kannada...")
results.append("=" * 60)
response_kannada = requests.post(ENDPOINT, headers=headers, json=payload_kannada)
results.append(f"Status: {response_kannada.status_code}")
if response_kannada.status_code == 200:
    results.append(f"SUCCESS! Audio length: {len(response_kannada.content)} bytes")
    # Save audio
    with open("test_kannada.mp3", "wb") as f:
        f.write(response_kannada.content)
    results.append("Saved to test_kannada.mp3")
else:
    results.append(f"ERROR Response Text: {response_kannada.text}")
    try:
        error_json = response_kannada.json()
        results.append(f"ERROR JSON: {json.dumps(error_json, indent=2)}")
    except:
        pass

# Write results to file
with open("test_results.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(results))

print("\n".join(results))
print("\n\nResults saved to test_results.txt")
