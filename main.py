from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os

app = FastAPI(title="JattGamerzFlix Backend")

# Enable CORS for the mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment Variables (Set these in Render/Railway dashboard)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "YOUR_YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "YOUR_CHANNEL_ID")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "super_secret_token_123")

# In-memory DB for Stream Keys (Use Redis/PostgreSQL for production)
stream_keys_db = {
    "youtube": "",
    "instagram": ""
}

class StreamKeys(BaseModel):
    youtube: str | None = None
    instagram: str | None = None

@app.get("/api/subs")
async def get_subscriber_count():
    """Fetch Live Subscriber Count from YouTube Data API v3"""
    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={YOUTUBE_CHANNEL_ID}&key={YOUTUBE_API_KEY}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                sub_count = data["items"][0]["statistics"]["subscriberCount"]
                return {"subscriberCount": int(sub_count)}
        raise HTTPException(status_code=400, detail="Failed to fetch YouTube stats")

@app.post("/api/keys")
async def update_stream_keys(keys: StreamKeys, authorization: str = Header(None)):
    """Securely update RTMP Stream Keys"""
    if authorization != f"Bearer {ADMIN_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if keys.youtube: stream_keys_db["youtube"] = keys.youtube
    if keys.instagram: stream_keys_db["instagram"] = keys.instagram
    return {"message": "Keys updated successfully"}

@app.get("/api/keys")
async def get_stream_keys(authorization: str = Header(None)):
    """Retrieve RTMP Stream Keys for the mobile app"""
    if authorization != f"Bearer {ADMIN_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    return stream_keys_db
