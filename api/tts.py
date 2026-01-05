from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
import edge_tts
import os
import uuid
import re
import asyncio
from typing import List
from database import get_database
from models import TTSRequest, TTSHistory, UserInDB, TTSSettings, PublicStory
from auth import get_current_user
from bson import ObjectId
from api import bhashini # Import Bhashini service

router = APIRouter(prefix="/tts", tags=["tts"])

OUTPUT_DIR = "outputs"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Comprehensive Mapping of personas to edge-tts voices
VOICE_MAPPING = {
    # Original Narrators
    "The Narrator": "en-US-GuyNeural",
    "Dr. Kathe": "en-US-EmmaNeural",
    "Deep Mystery": "en-GB-RyanNeural",
    "Soft Whisper": "en-US-JennyNeural",
    
    # Hindi Voices
    "Swara (Female)": "hi-IN-SwaraNeural",
    "Neerja (Female)": "hi-IN-NeerjaNeural",
    "Madhur (Male)": "hi-IN-MadhurNeural",
    "Arjun (Male - Expressive)": "hi-IN-ArjunNeural",
    "Aarti (Female - Expressive)": "hi-IN-AartiNeural",
    
    # English (India)
    "Neerja (IN - Female)": "en-IN-NeerjaNeural",
    "Prabhat (IN - Male)": "en-IN-PrabhatNeural",
    "Aashi (IN - Female)": "en-IN-AashiNeural",
    "Arjun (IN - Male Expressive)": "en-IN-ArjunNeural",
    "Aarti (IN - Female Expressive)": "en-IN-AartiNeural",
    
    # Regional Indian Languages
    "Bashkar (Bengali - Male)": "bn-IN-BashkarNeural",
    "Tanishaa (Bengali - Female)": "bn-IN-TanishaaNeural",
    "Sapna (Kannada - Female)": "kn-IN-SapnaNeural",
    "Gagan (Kannada - Male)": "kn-IN-GaganNeural",
    "Sobhana (Malayalam - Female)": "ml-IN-SobhanaNeural",
    "Midhun (Malayalam - Male)": "ml-IN-MidhunNeural",
    "Aarohi (Marathi - Female)": "mr-IN-AarohiNeural",
    "Manohar (Marathi - Male)": "mr-IN-ManoharNeural",
    "Yashica (Assamese - Female)": "as-IN-YashicaNeural",
    "Punjabi (Female)": "pa-IN-OjasNeural",
    "Punjabi (Male)": "pa-IN-GaganNeural",
    "Odia (Female)": "or-IN-SubhasiniNeural"
}

@router.get("/bhashini/config")
async def get_bhashini_configuration():
    return await bhashini.get_bhashini_config()

@router.post("/generate")
async def generate_audio(request: TTSRequest, current_user: UserInDB = Depends(get_current_user)):
    try:
        # PREMIUM MODE HANDLER
        if request.is_premium:
            if request.segments:
                # TODO: Implement multi-segment support for Bhashini if needed
                # For now, we'll join text or handle first segment
                text_to_process = " ".join([seg.text for seg in request.segments])
                # Use settings from first segment
                target_lang = request.segments[0].language
                target_voice = request.segments[0].persona
                base_settings = TTSSettings(
                    language=target_lang,
                    persona=target_voice,
                    speed=request.segments[0].speed,
                    pitch=request.segments[0].pitch,
                    is_premium=True
                )
            else:
                text_to_process = request.text
                target_lang = request.settings.language
                target_voice = request.settings.persona
                base_settings = request.settings

            # Generate with Bhashini
            print(f"DEBUG: Premium Bhashini Request: {text_to_process[:50]}... Lang: {target_lang}")
            
            # Since Bhashini doesn't support streaming easily in this setup, we wait for full audio
            # Note: This is a placeholder call. Real implementation needs specific Bhashini logic.
            # For now, Bhashini service raises exception or returns mock data.
            audio_data = await bhashini.generate_bhashini_audio(text_to_process, target_lang, target_voice)
            
            # Save to file
            if request.title:
                safe_title = "".join([c for c in request.title if c.isalnum() or c in (' ', '-', '_')]).strip()
                safe_title = safe_title.replace(' ', '_')
                filename = f"{safe_title}_{uuid.uuid4().hex[:8]}.mp3" if safe_title else f"{uuid.uuid4()}.mp3"
            else:
                filename = f"{uuid.uuid4()}.mp3"
                
            filepath = os.path.join(OUTPUT_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(audio_data) # Assuming byte content
                
            # History Saving (Common logic)
            db = await get_database()
            history = TTSHistory(
                user_id=str(current_user.id),
                title=request.title,
                text=text_to_process.strip(),
                settings=base_settings,
                audio_path=filepath,
                is_premium=True
            )
            
            history_dict = history.dict(by_alias=True)
            if "_id" in history_dict and not isinstance(history_dict["_id"], ObjectId):
                    history_dict["_id"] = ObjectId(str(history_dict["_id"]))
                    
            await db.tts_history.insert_one(history_dict)
            
            return {
                "audio_url": f"/outputs/{filename}",
                "filename": filename
            }

        # STANDARD EDGE-TTS FLOW
        script_segments = []
        combined_text = ""
        base_settings = None # This will hold the settings for history

        # If explicit segments are provided (Structured Multi-Narration)
        if request.segments:
            if not request.segments:
                raise HTTPException(status_code=400, detail="Segments array cannot be empty if provided.")
            
            for seg in request.segments:
                speed_percent = int((seg.speed - 1.0) * 100)
                speed_str = f"{speed_percent:+d}%"
                pitch_str = f"{seg.pitch:+d}Hz"
                voice = VOICE_MAPPING.get(seg.persona, "en-US-GuyNeural")
                script_segments.append({
                    "text": seg.text,
                    "voice": voice,
                    "speed": speed_str,
                    "pitch": pitch_str
                })
                combined_text += seg.text + " "
            
            # Use the settings from the first segment as a placeholder for history
            # Assuming all segments share the same language for history purposes, or it's not critical
            base_settings = TTSSettings(
                language=request.segments[0].language,
                persona=request.segments[0].persona,
                speed=request.segments[0].speed,
                pitch=request.segments[0].pitch,
                style_instruction=request.segments[0].style_instruction
            )
        else:
            # Traditional Single Narration with heuristic parsing
            if not request.text or not request.settings:
                raise HTTPException(status_code=400, detail="Text and settings are required for single narration mode.")
            
            combined_text = request.text
            base_settings = request.settings
            
            narrator_voice = VOICE_MAPPING.get(request.settings.persona, "en-US-GuyNeural")
            speed_percent = int((request.settings.speed - 1.0) * 100)
            speed_str = f"{speed_percent:+d}%"
            pitch_str = f"{request.settings.pitch:+d}Hz"
            
            lines = request.text.split('\n')
            
            char_voice_hints = {
                "Anna": "en-IN-NeerjaNeural",
                "Ben": "en-IN-ArjunNeural",
                "Owner": "en-IN-PrabhatNeural",
                "Narrator": narrator_voice,
                "Doctor": "en-IN-PrabhatNeural",
                "Friend": "en-IN-PrabhatNeural",
                "Girl": "en-IN-AashiNeural",
                "Boy": "en-IN-ArjunNeural"
            }

            # Regex to detect "Name: Dialogue" or "Name – Dialogue"
            # Matches "Anna:", "Old Man:", "Character Name –"
            script_pattern = re.compile(r'^([A-Z][a-zA-Z\s]+)[:–]\s*(.*)$')

            def get_best_voice(text, primary_voice):
                # Check for Kannada characters
                if re.search(r'[\u0C80-\u0CFF]', text):
                    return "kn-IN-SapnaNeural"
                # Check for Devanagari (Hindi/Marathi)
                if re.search(r'[\u0900-\u097F]', text):
                    return "hi-IN-SwaraNeural"
                # Check for Bengali
                if re.search(r'[\u0980-\u09FF]', text):
                    return "bn-IN-TanishaaNeural"
                # Check for Malayalam
                if re.search(r'[\u0D00-\u0D7F]', text):
                    return "ml-IN-SobhanaNeural"
                return primary_voice

            for line in lines:
                line = line.strip()
                if not line: continue
                
                # Skip metadata lines FIRST
                if line.lower().startswith(("title:", "characters:", "story:")):
                    print(f"DEBUG: Skipping metadata line: {line}")
                    continue

                match = script_pattern.match(line)
                if match:
                    char_name = match.group(1).strip()
                    dialogue = match.group(2).strip()
                    
                    # Check if this name is actually a metadata tag we missed
                    if char_name.lower() in ["title", "characters", "story"]:
                        continue

                    # Remove smart quotes from dialogue
                    dialogue = dialogue.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'").strip('" ')
                    
                    if not dialogue: continue
                    
                    voice = char_voice_hints.get(char_name, narrator_voice)
                    # Auto-detect language if the assigned voice is English but text is not
                    if "en-" in voice.lower():
                        voice = get_best_voice(dialogue, voice)
                        
                    script_segments.append({"text": dialogue, "voice": voice, "speed": speed_str, "pitch": pitch_str})
                else:
                    sanitized_line = line.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
                    voice = narrator_voice
                    # Auto-detect language for narrator text if narrator is English
                    if "en-" in voice.lower():
                        voice = get_best_voice(sanitized_line, voice)
                        
                    script_segments.append({"text": sanitized_line, "voice": voice, "speed": speed_str, "pitch": pitch_str})

            # If no segments detected, treat as one block
            if not script_segments:
                sanitized_text = request.text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
                voice = get_best_voice(sanitized_text, narrator_voice) if "en-" in narrator_voice.lower() else narrator_voice
                script_segments = [{"text": sanitized_text, "voice": voice, "speed": speed_str, "pitch": pitch_str}]

        # Create filename - use title if available
        if request.title:
            safe_title = "".join([c for c in request.title if c.isalnum() or c in (' ', '-', '_')]).strip()
            safe_title = safe_title.replace(' ', '_')
            if not safe_title:
                filename = f"{uuid.uuid4()}.mp3"
            else:
                filename = f"{safe_title}_{uuid.uuid4().hex[:8]}.mp3"
        else:
            filename = f"{uuid.uuid4()}.mp3"
            
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        generated_count = 0
        print(f"DEBUG: Starting generation for {len(script_segments)} segments")
        
        with open(filepath, "wb") as final_file:
            for i, seg in enumerate(script_segments):
                text_chunk = seg["text"]
                voice_id = seg["voice"]
                rate = seg["speed"]
                pitch = seg["pitch"]
                
                if not text_chunk.strip(): continue
                
                print(f"DEBUG: Processing Segment {i} | Voice: {voice_id} | Text: {text_chunk[:30]}...")
                
                try:
                    communicate = edge_tts.Communicate(
                        text_chunk, 
                        voice_id, 
                        rate=rate, 
                        pitch=pitch
                    )
                    
                    has_audio = False
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            final_file.write(chunk["data"])
                            has_audio = True
                    
                    if has_audio:
                        generated_count += 1
                        print(f"DEBUG: Segment {i} SUCCESS")
                    else:
                        print(f"DEBUG: Segment {i} WARNING: No audio produced for text: '{text_chunk}'")
                
                except Exception as seg_err:
                    print(f"DEBUG: Segment {i} FAILED: {str(seg_err)}")
                    # Continue to next segment instead of failing entire story
                    continue
        
        if generated_count == 0:
            raise Exception("Failed to generate any audio segments. Check if your script contains valid text.")

        # Save to history
        db = await get_database()
        history = TTSHistory(
            user_id=str(current_user.id),
            title=request.title,
            text=combined_text.strip(), # Use combined_text for history
            settings=base_settings, # Use base_settings for history
            audio_path=filepath
        )
        
        history_dict = history.dict(by_alias=True)
        if "_id" in history_dict and not isinstance(history_dict["_id"], ObjectId):
             history_dict["_id"] = ObjectId(str(history_dict["_id"]))
             
        await db.tts_history.insert_one(history_dict)
        
        return {
            "audio_url": f"/outputs/{filename}",
            "filename": filename
        }

    except Exception as e:
        import traceback
        error_msg = f"CRITICAL ERROR in generate_audio: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        with open("error.log", "a", encoding="utf-8") as f:
            f.write(error_msg + "\n")
        raise HTTPException(status_code=500, detail=f"TTS Generation failed: {str(e)}")

@router.delete("/history/{history_id}")
async def delete_history(history_id: str, current_user: UserInDB = Depends(get_current_user)):
    db = await get_database()
    
    # Handle both ObjectId and string ID storage
    query_id = history_id
    try:
        obj_id = ObjectId(history_id)
        query_id = {"$in": [obj_id, history_id]}
    except:
        pass
        
    history_item = await db.tts_history.find_one({"_id": query_id, "user_id": str(current_user.id)})
    if not history_item:
        raise HTTPException(status_code=404, detail="Story not found or unauthorized")
        
    # Delete file from disk
    audio_path = history_item.get("audio_path")
    if audio_path and os.path.exists(audio_path):
        try:
            os.remove(audio_path)
        except Exception as e:
            print(f"DEBUG: Failed to delete file {audio_path}: {e}")
            
    # Delete from database using the actual ID found
    await db.tts_history.delete_one({"_id": history_item["_id"]})
    
    # Also remove from public stories if present
    await db.public_stories.delete_one({"original_history_id": history_id})
    return {"message": "Story deleted successfully"}

@router.get("/history", response_model=List[TTSHistory])
async def get_history(current_user: UserInDB = Depends(get_current_user)):
    db = await get_database()
    cursor = db.tts_history.find({"user_id": str(current_user.id)}).sort("created_at", -1)
    history = await cursor.to_list(length=100)
    return history

@router.post("/public/{history_id}")
async def toggle_public_story(history_id: str, current_user: UserInDB = Depends(get_current_user)):
    db = await get_database()
    
    # Handle both ObjectId and string ID storage
    query_id = history_id
    try:
        obj_id = ObjectId(history_id)
        query_id = {"$in": [obj_id, history_id]}
    except:
        pass

    # Verify ownership
    history_item = await db.tts_history.find_one({"_id": query_id, "user_id": str(current_user.id)})
    if not history_item:
        raise HTTPException(status_code=404, detail="Story not found or unauthorized")
    
    real_id = history_item["_id"] # Use the actual ID type from DB

    # Check if already public
    existing_public = await db.public_stories.find_one({"original_history_id": history_id})

    try:
        if existing_public:
            # Toggle OFF: Delete from public AND update history
            await db.public_stories.delete_one({"_id": existing_public["_id"]})
            await db.tts_history.update_one({"_id": real_id}, {"$set": {"is_public": False}})
            return {"status": "removed", "message": "Story removed from public library"}
        else:
            # Ensure settings is valid TTSSettings object
            settings_data = history_item["settings"]
            # Handle potential dictionary vs object
            if isinstance(settings_data, dict):
                settings_obj = TTSSettings(**settings_data)
            else:
                settings_obj = settings_data

            # Toggle ON: Add to public AND update history
            public_story = PublicStory(
                original_history_id=history_id,
                user_id=str(current_user.id),
                title=history_item.get("title"),
                text=history_item["text"],
                settings=settings_obj,
                audio_path=history_item["audio_path"]
            )
            await db.public_stories.insert_one(public_story.model_dump(by_alias=True))
            await db.tts_history.update_one({"_id": real_id}, {"$set": {"is_public": True}})
            return {"status": "added", "message": "Story published to public library"}
    except Exception as e:
        print(f"ERROR in toggle_public: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Public toggle failed: {str(e)}")

@router.get("/public", response_model=List[PublicStory])
async def get_public_stories():
    db = await get_database()
    cursor = db.public_stories.find().sort("created_at", -1)
    stories = await cursor.to_list(length=100)
    return stories

@router.post("/upload")
async def upload_audio(
    file: UploadFile = File(...),
    name: str = Form(...),
    current_user: UserInDB = Depends(get_current_user)
):
    if not file.filename.endswith(('.mp3', '.wav', '.ogg')):
        raise HTTPException(status_code=400, detail="Invalid file format. Only audio files allowed.")

    # Generate unique filename
    file_id = str(uuid.uuid4())
    extension = os.path.splitext(file.filename)[1]
    filename = f"upload_{file_id}{extension}"
    file_path = os.path.join(OUTPUT_DIR, filename)

    # Save file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Create DB entry
    db = await get_database()
    history_item = TTSHistory(
        user_id=str(current_user.id),
        title=name,
        text=name, # Using text field for the story name
        settings=TTSSettings(
            language="Uploaded",
            persona="User Audio",
            speed=1.0,
            pitch=0,
            style_instruction=""
        ),
        audio_path=file_path
    )
    
    new_story_dict = history_item.model_dump(by_alias=True, exclude={"id"})
    new_story = await db.tts_history.insert_one(new_story_dict)
    created_story = await db.tts_history.find_one({"_id": new_story.inserted_id})
    return created_story
