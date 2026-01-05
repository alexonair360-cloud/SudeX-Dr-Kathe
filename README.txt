================================================================================
KANNADA STORY NARRATION - TEXT TO SPEECH
================================================================================

This project generates Kannada audio narration for a 15-scene story using
Microsoft Edge TTS (Text-to-Speech) technology.

================================================================================
FEATURES
================================================================================

✓ High-quality Kannada female voice (Sapna Neural)
✓ Slow, clear, emotional storytelling style
✓ 15 scene-wise audio outputs
✓ No Microsoft C++ Build Tools required
✓ Works on Windows without complex setup
✓ Unlimited text-to-speech generation

================================================================================
REQUIREMENTS
================================================================================

1. Python 3.7 or higher
2. Internet connection (for first-time voice model download)
3. edge-tts library

================================================================================
INSTALLATION
================================================================================

Step 1: Install the required library
----------------------------------------
pip install edge-tts

That's it! No complex build tools needed.

================================================================================
HOW TO RUN
================================================================================

Simply run the Python script:
----------------------------------------
python kannada_story_edge.py

The script will:
1. Create an "outputs" folder (if it doesn't exist)
2. Generate 15 audio files (scene_01.wav to scene_15.wav)
3. Each file contains the narration for one scene
4. Speech rate is set to -20% for slower storytelling

================================================================================
CODE EXPLANATION
================================================================================

The script (kannada_story_edge.py) works as follows:

1. IMPORTS
   - os: For creating the output directory
   - asyncio: For asynchronous audio generation
   - edge_tts: Microsoft Edge TTS library

2. CONFIGURATION
   - VOICE: "kn-IN-SapnaNeural" (Kannada female voice)
   - RATE: "-20%" (slower speech for storytelling)

3. SCENES DICTIONARY
   - Contains 15 Kannada text scenes
   - Each scene is a separate story segment

4. GENERATE_SCENE FUNCTION
   - Takes scene name and text as input
   - Creates TTS communication object
   - Saves audio to outputs/scene_XX.wav

5. MAIN FUNCTION
   - Iterates through all 15 scenes
   - Generates audio for each scene
   - Displays progress messages

6. EXECUTION
   - asyncio.run(main()) runs the async main function
   - Generates all scenes sequentially

================================================================================
OUTPUT
================================================================================

After running, you'll have 15 WAV files in the "outputs" folder:

outputs/
├── scene_01.wav
├── scene_02.wav
├── scene_03.wav
├── scene_04.wav
├── scene_05.wav
├── scene_06.wav
├── scene_07.wav
├── scene_08.wav
├── scene_09.wav
├── scene_10.wav
├── scene_11.wav
├── scene_12.wav
├── scene_13.wav
├── scene_14.wav
└── scene_15.wav

Each file contains high-quality Kannada narration with a natural female voice.

================================================================================
CUSTOMIZATION
================================================================================

To modify the voice or speed:

1. Change VOICE:
   - Female: "kn-IN-SapnaNeural"
   - Male: "kn-IN-GaganNeural"

2. Change RATE:
   - Faster: "+10%" or "+20%"
   - Slower: "-30%" or "-40%"
   - Normal: "0%"

3. Add more scenes:
   - Add entries to the scenes dictionary
   - Follow the format: "scene_XX": "Kannada text here"

================================================================================
TROUBLESHOOTING
================================================================================

Problem: ModuleNotFoundError: No module named 'edge_tts'
Solution: Run "pip install edge-tts"

Problem: No internet connection
Solution: Edge-TTS requires internet for first download. After that, 
         voices are cached locally.

Problem: Audio files not generated
Solution: Check if "outputs" folder has write permissions

================================================================================
WHY EDGE-TTS INSTEAD OF COQUI XTTS?
================================================================================

Coqui XTTS v2 requires:
- Microsoft Visual C++ Build Tools (6GB download)
- Complex compilation process
- May fail on some Windows systems

Edge-TTS advantages:
- Simple pip install
- No build tools required
- High-quality Microsoft neural voices
- Works reliably on Windows
- Faster setup and execution

================================================================================
TECHNICAL NOTES
================================================================================

- Audio format: WAV (uncompressed)
- Sample rate: Determined by Edge-TTS (typically 24kHz)
- Voice type: Neural TTS (high quality)
- Language code: kn-IN (Kannada - India)
- Asynchronous execution for better performance

================================================================================
STORY CONTENT
================================================================================

The story is about a teacher sharing memories of their grandparents with
students. It's a touching narrative about:

- Traditional marriages
- Hard work and dedication
- Love without modern technology
- Life lessons from elders
- A grandfather who was like a king without a crown

Narrated in pure Kannada with emotional, cinematic storytelling style.

================================================================================
END OF README
================================================================================

Inital Run 

cd backend
pip install -r requirements.txt
python kannada_story_edge.py