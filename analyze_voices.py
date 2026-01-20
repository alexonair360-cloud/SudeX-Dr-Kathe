import json

# Load and analyze voices.json
with open("voices.json", "r", encoding="utf-8") as f:
    data = json.load(f)

voices = data["voices"]

# Extract unique native languages
languages = set()
voice_ids_by_lang = {}

for voice in voices:
    lang = voice["nativeLanguage"]
    voice_id = voice["id"]
    languages.add(lang)
    
    if lang not in voice_ids_by_lang:
        voice_ids_by_lang[lang] = []
    voice_ids_by_lang[lang].append({
        "id": voice_id,
        "name": voice["name"],
        "styles": voice["supportedStyles"]
    })

print("Available Languages:")
print("=" * 60)
for lang in sorted(languages):
    print(f"\n{lang}:")
    print(f"  Total voices: {len(voice_ids_by_lang[lang])}")
    print(f"  Voice IDs: {[v['id'] for v in voice_ids_by_lang[lang]]}")

# Save summary
with open("voice_summary.txt", "w", encoding="utf-8") as f:
    f.write("BHASHINI AVAILABLE LANGUAGES AND VOICES\n")
    f.write("=" * 60 + "\n\n")
    for lang in sorted(languages):
        f.write(f"{lang}:\n")
        f.write(f"  Total voices: {len(voice_ids_by_lang[lang])}\n")
        for v in voice_ids_by_lang[lang]:
            f.write(f"    - {v['id']}: {v['name']}\n")
            f.write(f"      Styles: {', '.join(v['styles'])}\n")
        f.write("\n")

print("\n\nSummary saved to voice_summary.txt")
