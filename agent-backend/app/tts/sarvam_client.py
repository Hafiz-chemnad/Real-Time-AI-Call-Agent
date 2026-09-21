import os

from pipecat.services.sarvam.tts import SarvamTTSService


def get_sarvam_tts_service(speaker: str | None = None) -> SarvamTTSService:
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise ValueError("SARVAM_API_KEY is missing from environment variables.")

    voice_speaker = speaker or os.getenv("SARVAM_TTS_SPEAKER", "shubh")

    masked_key = f"{api_key[:5]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
    print(f"\n🔐 Authenticating with Sarvam TTS Key: {masked_key}")

    # FIXED: Using the new Settings class required by Pipecat
    tts_service = SarvamTTSService(
        api_key=api_key,
        settings=SarvamTTSService.Settings(
            model="bulbul:v3",
            voice=voice_speaker,
        )
    )

    return tts_service