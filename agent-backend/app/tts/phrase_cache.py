# app/tts/phrase_cache.py
import os
import wave
from pipecat.frames.frames import AudioRawFrame


class PhraseCache:
    def __init__(self):
        # We will load pre-rendered 8kHz mu-law or 16kHz PCM audio files into memory
        self.cache_dir = os.path.join(os.path.dirname(__file__), "cached_audio")
        self.phrases = {}
        self._load_cache()

    def _load_cache(self):
        """Loads static filler phrases into memory for < 50ms playback."""
        # Example: "Let me check that for you..."
        filler_path = os.path.join(self.cache_dir, "let_me_check.wav")
        if os.path.exists(filler_path):
            # Use the wave module to properly strip the WAV header and
            # extract only raw PCM sample data — passing the raw file bytes
            # (including the ~44-byte header) directly into an AudioRawFrame
            # causes that header to be played as garbage audio, producing an
            # audible pop/static artifact at the start of playback.
            with wave.open(filler_path, 'rb') as wf:
                self.phrases["let_me_check"] = {
                    "audio": wf.readframes(wf.getnframes()),
                    "sample_rate": wf.getframerate(),
                    "num_channels": wf.getnchannels(),
                }

    def get_filler_frame(self, phrase_key: str) -> AudioRawFrame:
        """Returns a Pipecat AudioRawFrame ready to instantly stream."""
        phrase = self.phrases.get(phrase_key)
        if phrase:
            # Use the actual sample rate/channel count read from the file,
            # rather than hardcoding 8kHz/mono — avoids silently playing
            # audio at the wrong speed/pitch if the source file ever changes.
            return AudioRawFrame(
                audio=phrase["audio"],
                sample_rate=phrase["sample_rate"],
                num_channels=phrase["num_channels"],
            )
        return None