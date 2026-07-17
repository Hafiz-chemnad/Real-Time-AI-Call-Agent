from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router as api_router

# 1. Initialize the FastAPI application
app = FastAPI(
    title="Project 1: Text Bot API",
    description="A RAG-based Text Bot using FastAPI and LLMs",
    version="1.0.0"
)

# 2. Configure CORS Middleware (Allows web/mobile frontends to talk to your API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# 3. Include your routes from api/routes.py
app.include_router(api_router)

# 4. Optional Root Endpoint (For testing if the server is running)
@app.get("/")
def root_check():
    return {"status": "online", "message": "Text Bot API is running!"}