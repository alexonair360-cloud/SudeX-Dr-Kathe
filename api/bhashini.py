import os
import requests
import json
from fastapi import HTTPException
from typing import Dict, List, Optional

# Bhashini API configuration
BHASHINI_API_KEY = os.getenv("BHASHINI_API_KEY", "")
BHASHINI_ENDPOINT = os.getenv("BHASHINI_ENDPOINT", "https://tts.bhashini.ai/v1")
BHASHINI_VOICES_URL = "https://app.bhashini.ai/voices.json"

# Cache for voice configuration
_voice_config_cache: Optional[Dict] = None

async def fetch_voice_configuration():
    """
    Fetches the voice configuration from Bhashini voices.json.
    Returns a mapping of languages to available voices and their supported styles.
    """
    global _voice_config_cache
    
    # Return cached config if available
    if _voice_config_cache is not None:
        return _voice_config_cache
    
    try:
        response = requests.get(BHASHINI_VOICES_URL, timeout=10)
        response.raise_for_status()
        voices_data = response.json()
        
        # Parse the voices array
        # Structure: {"voices": [{"id": "kn-f1", "name": "Kannada Female 1", "nativeLanguage": "Kannada", "supportedStyles": [...]}]}
        config = {
            "languages": [],
            "voices": {},
            "styles": {},
            "voice_map": {}  # Maps voice name to voice ID
        }
        
        if "voices" in voices_data and isinstance(voices_data["voices"], list):
            voices_list = voices_data["voices"]
            lang_set = set()
            
            for voice in voices_list:
                voice_id = voice.get("id", "")
                voice_name = voice.get("name", "")
                native_lang = voice.get("nativeLanguage", "")
                supported_styles = voice.get("supportedStyles", ["Neutral"])
                
                if not native_lang:
                    continue
                
                lang_set.add(native_lang)
                
                # Initialize language in voices dict
                if native_lang not in config["voices"]:
                    config["voices"][native_lang] = []
                
                # Add voice name to the language's voice list
                config["voices"][native_lang].append(voice_name)
                
                # Map voice name to voice ID
                config["voice_map"][voice_name] = voice_id
                
                # Store supported styles for this voice
                config["styles"][voice_name] = supported_styles
            
            # Create languages list
            config["languages"] = [{"code": lang.lower()[:2], "name": lang} for lang in sorted(lang_set)]
            
            # If no voices found, use fallback
            if not config["voices"]:
                print("WARNING: No voices found in voices.json, using fallback")
                return get_default_bhashini_config()
        else:
            print("WARNING: Invalid voices.json structure, using fallback")
            return get_default_bhashini_config()
        
        _voice_config_cache = config
        print(f"✅ Loaded {len(voices_list)} voices from Bhashini for {len(lang_set)} languages")
        return config
        
    except Exception as e:
        print(f"Failed to fetch Bhashini voice configuration: {str(e)}")
        # Return default configuration as fallback
        return get_default_bhashini_config()

def get_default_bhashini_config():
    """
    Returns a default Bhashini configuration based on known voice IDs.
    This serves as a fallback if voices.json cannot be fetched.
    """
    return {
        "languages": [
            {"code": "hi", "name": "Hindi"},
            {"code": "kn", "name": "Kannada"},
            {"code": "ta", "name": "Tamil"},
            {"code": "te", "name": "Telugu"},
            {"code": "mr", "name": "Marathi"},
            {"code": "bn", "name": "Bengali"},
            {"code": "gu", "name": "Gujarati"},
            {"code": "ml", "name": "Malayalam"},
            {"code": "pa", "name": "Punjabi"},
            {"code": "en", "name": "English"}
        ],
        "voices": {
            "hi": ["Hindi Female 1", "Hindi Female 2", "Hindi Female 3", "Hindi Male 1", "Hindi Male 2"],
            "kn": ["Kannada Female 1", "Kannada Female 2", "Kannada Male 1", "Kannada Male 2"],
            "ta": ["Tamil Female 1", "Tamil Female 2", "Tamil Male 1", "Tamil Male 2"],
            "te": ["Telugu Female 1", "Telugu Female 2", "Telugu Male 1", "Telugu Male 2"],
            "mr": ["Marathi Female 1", "Marathi Male 1"],
            "bn": ["Bengali Female 1", "Bengali Male 1"],
            "gu": ["Gujarati Female 1", "Gujarati Male 1"],
            "ml": ["Malayalam Female 1", "Malayalam Male 1"],
            "pa": ["Punjabi Female 1", "Punjabi Male 1"],
            "en": ["English Female 1", "English Male 1"]
        },
        "styles": {
            # Default styles available for most voices
            "default": ["Neutral", "Book", "Conversational"]
        }
    }

async def get_bhashini_config():
    """
    Returns the available languages, voices, and styles for Bhashini TTS.
    This endpoint is called by the frontend to populate dropdowns.
    """
    config = await fetch_voice_configuration()
    
    # Transform into frontend-friendly format
    # Frontend expects: { "Hindi": ["Voice1", "Voice2"], ... }
    result = {
        "languages": config.get("languages", []),
        "voices": {},
        "styles": config.get("styles", {})
    }
    
    # Map language codes to full names for voices
    lang_map = {lang["code"]: lang["name"] for lang in config.get("languages", [])}
    
    for lang_code, voice_list in config.get("voices", {}).items():
        lang_name = lang_map.get(lang_code, lang_code.capitalize())
        result["voices"][lang_name] = voice_list
    
    # Add default styles if not present
    if not result["styles"]:
        result["styles"]["default"] = ["Neutral", "Book", "Conversational"]
    
    return result

def map_language_to_code(language_name: str) -> str:
    """
    Maps a full language name to its language code.
    Example: "Hindi" -> "hi", "Kannada" -> "kn"
    """
    lang_mapping = {
        "Hindi": "hi",
        "Kannada": "kn",
        "Tamil": "ta",
        "Telugu": "te",
        "Marathi": "mr",
        "Bengali": "bn",
        "Gujarati": "gu",
        "Malayalam": "ml",
        "Punjabi": "pa",
        "English": "en"
    }
    return lang_mapping.get(language_name, "hi")  # Default to Hindi

def map_persona_to_voice_id(persona_name: str, language_code: str) -> str:
    """
    Maps a persona name to a Bhashini voice ID.
    Example: "Hindi Female 1" -> "hi-f1", "Kannada Male 2" -> "kn-m2"
    """
    # Extract gender and number from persona name
    # Format: "Language Gender Number" -> "lang-gender_initial+number"
    parts = persona_name.lower().split()
    
    if "female" in parts:
        gender = "f"
    elif "male" in parts:
        gender = "m"
    else:
        gender = "f"  # Default to female
    
    # Extract number (last part if it's a digit)
    number = "1"
    for part in reversed(parts):
        if part.isdigit():
            number = part
            break
    
    voice_id = f"{language_code}-{gender}{number}"
    return voice_id

async def generate_bhashini_audio(
    text: str, 
    language: str, 
    voice_id: str,
    voice_style: str = "Neutral",
    speech_rate: float = 1.0
) -> bytes:
    """
    Generates audio using the Bhashini TTS API.
    
    Args:
        text: The text to synthesize
        language: Language name (e.g., "Hindi", "Kannada")
        voice_id: The persona/voice name (e.g., "Hindi Female 3", "Kannada Female 1")
        voice_style: The speaking style (e.g., "Neutral", "Book", "Conversational")
        speech_rate: Speech rate multiplier (default 1.0 for normal speed)
    
    Returns:
        Audio data as bytes
    """
    if not BHASHINI_API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="Bhashini API Key not configured. Please set BHASHINI_API_KEY in environment variables."
        )
    
   # Get voice configuration to map voice name to ID
    config = await fetch_voice_configuration()
    voice_map = config.get("voice_map", {})
    
    # Lookup actual voice ID from the voice name
    bhashini_voice_id = voice_map.get(voice_id)
    
    if not bhashini_voice_id:
        # Fallback: Try to use voice_id directly in case it's already an ID
        bhashini_voice_id = voice_id
        print(f"WARNING: Voice '{voice_id}' not found in voice_map, using directly as ID")
    
    print(f"DEBUG Bhashini: Language='{language}', VoiceName='{voice_id}' -> VoiceID='{bhashini_voice_id}', Style='{voice_style}'")
    
    # Prepare request headers
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": BHASHINI_API_KEY
    }
    
    # Prepare request payload
    payload = {
        "text": text,
        "language": language,
        "voiceName": bhashini_voice_id,
        "voiceStyle": voice_style,
        "speechRate": speech_rate
    }
    
    print(f"DEBUG Bhashini Request Payload: {payload}")
    
    try:
        # Make API request to synthesize endpoint
        response = requests.post(
            f"{BHASHINI_ENDPOINT}/synthesize",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"DEBUG Bhashini Response Status: {response.status_code}")
        
        # Check for errors
        if response.status_code != 200:
            error_detail = f"Bhashini API returned status {response.status_code}"
            try:
                error_json = response.json()
                error_detail = error_json.get("detail", error_json.get("message", error_json.get("error", error_detail)))
                print(f"DEBUG Bhashini Error Response: {error_json}")
            except:
                error_detail = response.text or error_detail
                print(f"DEBUG Bhashini Error Text: {response.text[:500]}")
            
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Bhashini TTS Error: {error_detail}"
            )
        
        # Return the audio bytes
        audio_data = response.content
        
        if not audio_data:
            raise HTTPException(
                status_code=500,
                detail="Bhashini API returned empty audio data"
            )
        
        print(f"✅ Bhashini TTS Success: Generated {len(audio_data)} bytes for '{text[:50]}...'")
        return audio_data
        
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Bhashini API request timed out. Please try again."
        )
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Could not connect to Bhashini API. Please check your internet connection."
        )
    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is
    except Exception as e:
        print(f"❌ Bhashini Generation Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Bhashini TTS Error: {str(e)}"
        )
