from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from agent.automation_agent import suggest_automation, UserQuery, AutomationResponse
from typing import Dict, Any
import requests
import os

app = FastAPI(title="MSME Automation Helper")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root() -> Dict[str, str]:
    return {"message": "MSME Automation Helper API is running"}

@app.post("/api/automation-suggest")
async def get_automation_suggestion(query: UserQuery) -> AutomationResponse:
    try:
        return suggest_automation(query)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing automation suggestion: {str(e)}"
        )

@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe audio using AssemblyAI API."""
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AssemblyAI API key not set.")
    # Upload audio to AssemblyAI
    upload_url = "https://api.assemblyai.com/v2/upload"
    headers = {"authorization": api_key}
    audio_bytes = await file.read()
    upload_response = requests.post(upload_url, headers=headers, data=audio_bytes)
    if upload_response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to upload audio to AssemblyAI.")
    audio_url = upload_response.json()["upload_url"]
    # Request transcription
    transcript_url = "https://api.assemblyai.com/v2/transcript"
    transcript_response = requests.post(transcript_url, headers=headers, json={"audio_url": audio_url})
    if transcript_response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to start transcription.")
    transcript_id = transcript_response.json()["id"]
    # Poll for completion
    while True:
        poll_response = requests.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}", headers=headers)
        if poll_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to poll transcription.")
        status = poll_response.json()["status"]
        if status == "completed":
            return {"text": poll_response.json()["text"]}
        elif status == "failed":
            raise HTTPException(status_code=500, detail="Transcription failed.")
        import time; time.sleep(2)