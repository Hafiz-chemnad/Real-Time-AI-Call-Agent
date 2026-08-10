"""
Cartesia TTS client with a persistent WebSocket connection.
"""

from __future__ import annotations

import os
import time
from typing import AsyncIterator, Optional

from cartesia import AsyncCartesia


class CartesiaClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> None:

        self.api_key = api_key or os.getenv("CARTESIA_API_KEY")
        self.voice_id = voice_id or os.getenv("CARTESIA_VOICE_ID")

        self.model_id = (
            model_id
            or os.getenv("CARTESIA_MODEL_ID")
            or "sonic-3.5"
        )

        if not self.api_key:
            raise ValueError(
                "CARTESIA_API_KEY environment variable is required"
            )

        if not self.voice_id:
            raise ValueError(
                "CARTESIA_VOICE_ID environment variable is required"
            )

        self.client = AsyncCartesia(
            api_key=self.api_key
        )

        # Persistent WebSocket
        self.websocket = None

    async def _connect(self):
        """
        Create the persistent Cartesia WebSocket.
        """

        if self.websocket is None:

            print("[TTS] Opening persistent WebSocket...")

            manager = self.client.tts.websocket_connect()

            self.websocket = await manager.__aenter__()

            print("[TTS] Persistent WebSocket connected.")

        return self.websocket

    async def synthesize_stream(
        self,
        text: str,
    ) -> AsyncIterator[bytes]:
        """
        Stream PCM audio from Cartesia.

        The WebSocket connection remains open between
        multiple synthesis requests.
        """

        if not text.strip():
            return

        # -------------------------------------------------
        # Start total timer
        # -------------------------------------------------

        start = time.perf_counter()

        # -------------------------------------------------
        # Get persistent WebSocket
        # -------------------------------------------------

        ws = await self._connect()

        connection_ready = time.perf_counter()

        print(
            f"[TTS] Connection ready: "
            f"{(connection_ready - start) * 1000:.2f} ms"
        )

        # -------------------------------------------------
        # Create TTS context
        # -------------------------------------------------

        context_start = time.perf_counter()

        ctx = ws.context(
            model_id=self.model_id,
            voice={
                "mode": "id",
                "id": self.voice_id,
            },
            output_format={
                "container": "raw",
                "encoding": "pcm_s16le",
                "sample_rate": 16000,
            },
            language="en",
        )

        context_ready = time.perf_counter()

        print(
            f"[TTS] Context creation: "
            f"{(context_ready - context_start) * 1000:.2f} ms"
        )

        # -------------------------------------------------
        # Send text
        # -------------------------------------------------

        push_start = time.perf_counter()

        await ctx.push(text)

        push_done = time.perf_counter()

        print(
            f"[TTS] ctx.push(): "
            f"{(push_done - push_start) * 1000:.2f} ms"
        )

        # -------------------------------------------------
        # Tell Cartesia that input is complete
        # -------------------------------------------------

        no_input_start = time.perf_counter()

        await ctx.no_more_inputs()

        no_input_done = time.perf_counter()

        print(
            f"[TTS] no_more_inputs(): "
            f"{(no_input_done - no_input_start) * 1000:.2f} ms"
        )

        # -------------------------------------------------
        # Wait for audio
        # -------------------------------------------------

        server_wait_start = time.perf_counter()

        first_audio = True

        async for response in ctx.receive():

            # ---------------------------------------------
            # Audio chunk
            # ---------------------------------------------

            if response.type == "chunk" and response.audio:

                if first_audio:

                    now = time.perf_counter()

                    receive_wait_ms = (
                        now - server_wait_start
                    ) * 1000

                    total_ttfa_ms = (
                        now - start
                    ) * 1000

                    print(
                        f"[TTS] First audio after receive(): "
                        f"{receive_wait_ms:.2f} ms"
                    )

                    print(
                        f"[TTS] TOTAL TTFA: "
                        f"{total_ttfa_ms:.2f} ms"
                    )

                    first_audio = False

                yield response.audio

            # ---------------------------------------------
            # Cartesia error
            # ---------------------------------------------

            elif response.type == "error":

                raise RuntimeError(
                    response.message
                    or response.title
                    or "Cartesia TTS error"
                )

    async def close(self):
        """
        Close the persistent WebSocket.
        """

        if self.websocket is not None:

            print(
                "[TTS] Closing persistent WebSocket..."
            )

            await self.websocket.close()

            self.websocket = None

            print(
                "[TTS] WebSocket closed."
            )