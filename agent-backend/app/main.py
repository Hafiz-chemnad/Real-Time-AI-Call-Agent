from dotenv import load_dotenv
from app.api.v1 import businesses, tools, knowledge
from app.channels.chat import chat_endpoint
load_dotenv()  # <--- This loads your .env file automatically

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import test_endpoints
from app.channels.phone import twilio_webhook
from app.channels.voice_web import websocket_endpoint
import app.core.logging

app = FastAPI(title="Agent - AI Call Receptionist Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(test_endpoints.router)
app.include_router(twilio_webhook.router)
app.include_router(websocket_endpoint.router)
app.include_router(businesses.router)
app.include_router(tools.router)
app.include_router(knowledge.router)
app.include_router(chat_endpoint.router)

@app.get("/")
def health_check():
    return {"status": "ok"}