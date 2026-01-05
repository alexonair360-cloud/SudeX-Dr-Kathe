from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from api import users, tts

app = FastAPI(title="Dr Kathe TTS API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create outputs directory if not exists
if not os.path.exists("outputs"):
    os.makedirs("outputs")

# Mount static files for audio access
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Include Routers
app.include_router(users.router)
app.include_router(tts.router)

@app.get("/")
async def root():
    db_status = "connected"
    try:
        await get_database()
    except Exception:
        db_status = "error"
    return {
        "message": "Welcome to Dr Kathe TTS API",
        "status": "running",
        "database": db_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
