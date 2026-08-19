import os
from dotenv import load_dotenv
from pipecat.services.cartesia.tts import CartesiaTTSService

# Load environment variables so python can see CARTESIA_API_KEY
load_dotenv(override=True)

def get_fallback_tts_service():
    """
    Initializes the Tier 2 Cartesia TTS Service.
    Used automatically if ElevenLabs fails or times out.
    """
    api_key = os.getenv("CARTESIA_API_KEY")
    if not api_key:
        print("Warning: CARTESIA_API_KEY is missing. Tier 2 fallback disabled.")
        return None

    # Initialize Pipecat's Cartesia service
    tts_service = CartesiaTTSService(
        api_key=api_key,
        sample_rate=8000,  # <-- FIXED: Moved outside of Settings!
        settings=CartesiaTTSService.Settings(
            voice="f6141af3-5f94-418c-80ed-a45d450e7e2e", 
        )
    )

    return tts_service