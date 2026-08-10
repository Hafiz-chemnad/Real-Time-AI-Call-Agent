"""
Unified TTS engine.

Order:

1. Phrase cache
2. Cartesia
3. Kokoro
"""

from __future__ import annotations

from typing import AsyncIterator

from .cartesia_client import CartesiaClient
from .kokoro_local import KokoroLocal
from .phrase_cache import PhraseCache


class TTSEngine:

    def __init__(self) -> None:
        self.cache = PhraseCache()

        self.cartesia = None
        self.kokoro = None

        self._load_services()

    def _load_services(self) -> None:

        # Tier 1: Cartesia
        try:
            self.cartesia = CartesiaClient()
            print("Cartesia TTS: available")
        except Exception as exc:
            self.cartesia = None
            print(f"Cartesia TTS unavailable: {exc}")

        # Tier 2: Kokoro
        try:
            self.kokoro = KokoroLocal()
            print("Kokoro TTS: available")
        except Exception as exc:
            self.kokoro = None
            print(f"Kokoro TTS unavailable: {exc}")

    async def synthesize(
        self,
        text: str,
    ) -> AsyncIterator[bytes]:

        text = text.strip()

        if not text:
            return

        # ---------------------------------------------
        # Tier 0: Phrase cache
        # ---------------------------------------------

        cached = self.cache.get(text)

        if cached is not None:
            print("TTS: phrase cache HIT")
            yield cached
            return

        # ---------------------------------------------
        # Tier 1: Cartesia
        # ---------------------------------------------

        if self.cartesia is not None:

            try:
                received = False

                print("TTS: using Cartesia")

                async for audio in self.cartesia.synthesize_stream(text):
                    received = True
                    yield audio

                if received:
                    return

            except Exception as exc:
                print(f"Cartesia failed: {exc}")

        # ---------------------------------------------
        # Tier 2: Kokoro
        # ---------------------------------------------

        if self.kokoro is not None:

            try:
                print("TTS: using Kokoro")

                audio = self.kokoro.synthesize(text)

                if audio:
                    yield audio
                    return

            except Exception as exc:
                print(f"Kokoro failed: {exc}")

        raise RuntimeError(
            "All TTS providers failed."
        )