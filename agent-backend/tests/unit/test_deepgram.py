import httpx
import threading

from deepgram import DeepgramClient
from deepgram.core.events import EventType

DEEPGRAM_API_KEY = "082c8851c8e202d7ebb0221372a0c64f1b87cd7b"

# Note: This is an English stream, update accordingly for other languages
STREAM_URL = "https://playerservices.streamtheworld.com/api/livestream-redirect/CSPANRADIOAAC.aac"

client = DeepgramClient(api_key=DEEPGRAM_API_KEY)

# --- THE FIX IS HERE: model="nova-2" ---
with client.listen.v1.connect(
    model="nova-2",
    language="en",
    smart_format=True,
) as connection:
    ready = threading.Event()

    def on_message(result):
        event_type = result.type
        if event_type == "Results":
            channel = result.channel
            alt = channel.alternatives[0]
            transcript = alt.transcript
            if transcript:
                print(transcript)

    connection.on(EventType.OPEN, lambda _: ready.set())
    connection.on(EventType.MESSAGE, on_message)

    def stream():
        ready.wait()
        with httpx.stream("GET", STREAM_URL, follow_redirects=True) as response:
            for chunk in response.iter_bytes():
                connection.send_media(chunk)

    threading.Thread(target=stream, daemon=True).start()

    print(f"Transcribing {STREAM_URL}...")
    connection.start_listening()