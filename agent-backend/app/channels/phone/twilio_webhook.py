import os
import json
from fastapi import APIRouter, Request, Response, WebSocket, WebSocketDisconnect, HTTPException, Depends
from twilio.request_validator import RequestValidator

from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketTransport, FastAPIWebsocketParams
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.frames.frames import EndFrame

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams

from app.channels.phone.pipecat_pipeline import run_pipecat_pipeline

router = APIRouter()

class TwilioFrameSerializerWithStop(TwilioFrameSerializer):
    """Twilio's base serializer silently drops the 'stop' event (hangup) —
    only 'media' and 'dtmf' are handled. This subclass converts 'stop' into
    a proper EndFrame so the pipeline shuts down gracefully on hangup instead
    of sitting idle until Pipecat's unrelated idle-timeout eventually fires."""

    async def deserialize(self, data: str | bytes):
        try:
            message = json.loads(data)
            if message.get("event") == "stop":
                return EndFrame()
        except (json.JSONDecodeError, TypeError):
            pass
        return await super().deserialize(data)

async def validate_twilio_request(request: Request):
    twilio_signature = request.headers.get("X-Twilio-Signature")
    if not twilio_signature:
        raise HTTPException(status_code=403, detail="Missing Twilio signature")

    url = str(request.url)
    if url.startswith("http://") and "ngrok.io" in url or "ngrok-free.app" in url:
        url = url.replace("http://", "https://")

    form_data = await request.form()
    post_vars = dict(form_data)

    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if not auth_token:
        raise HTTPException(status_code=500, detail="TWILIO_AUTH_TOKEN not configured")

    validator = RequestValidator(auth_token)
    
    if not validator.validate(url, post_vars, twilio_signature):
        print("🚨 SECURITY ALERT: Rejected invalid Twilio signature!")
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

@router.post("/twilio/inbound/{business_id}")
async def handle_incoming_call(
    business_id: str,
    request: Request,
    _: None = Depends(validate_twilio_request),
):
    host = request.headers.get("host")
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Connect>
            <Stream url="wss://{host}/ws/twilio/{business_id}" />
        </Connect>
    </Response>
    """
    return Response(content=twiml, media_type="application/xml")

@router.websocket("/ws/twilio/{business_id}")
async def twilio_ws_endpoint(websocket: WebSocket, business_id: str):
    await websocket.accept()
    call_sid = None  

    try:
        start_data = None
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg.get('event') == 'start':
                start_data = msg
                break
            elif msg.get('event') == 'connected':
                continue  
            elif msg.get('event') == 'stop':
                print(f"Call ended by user for business {business_id}.")
                await websocket.close()
                return
            else:
                await websocket.close()
                return

        stream_sid = start_data['start']['streamSid']
        call_sid = start_data['start']['callSid']
        account_sid = start_data['start']['accountSid']
        auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")

        serializer = TwilioFrameSerializerWithStop(
            stream_sid=stream_sid,
            account_sid=account_sid,
            auth_token=auth_token,
            call_sid=call_sid,
            params=TwilioFrameSerializer.InputParams(auto_hang_up=False)
        )

        vad_analyzer = SileroVADAnalyzer(params=VADParams(
            confidence=0.7, 
            start_secs=0.2, 
            stop_secs=0.8, 
            min_volume=0.08,  # Increased mic sensitivity for Twilio audio streams[cite: 10]
        ))

        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_in_enabled=True,
                audio_in_sample_rate=16000,
                audio_out_enabled=True,
                add_wav_header=False,
                vad_enabled=True,
                vad_analyzer=vad_analyzer,
                vad_audio_passthrough=True,
                serializer=serializer
            )
        )

        await run_pipecat_pipeline(transport, call_sid, account_sid, auth_token, business_id)

    except WebSocketDisconnect:
        print("Twilio WebSocket disconnected normally.")
    except Exception as e:
        print(f"Fatal error in Twilio WebSocket: {e}")
    finally:
        print(f"Cleaning up resources for call {call_sid or 'unknown (no start event received)'}")