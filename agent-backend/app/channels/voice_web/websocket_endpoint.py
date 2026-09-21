# app/channels/voice_web/websocket_endpoint.py
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.transports.base_transport import TransportParams

from .pipecat_pipeline import run_webrtc_pipeline

router = APIRouter()

_active_connections: dict[str, SmallWebRTCConnection] = {}


@router.post("/webrtc/connect")
async def webrtc_connect_endpoint(request: Request):
    """Catches the WebRTC SDP offer from the dashboard's microphone testing widget."""
    try:
        offer = await request.json()
        pc_id = offer.get("pc_id")
        business_id = offer.get("business_id")

        if not business_id:
            return JSONResponse(
                content={"error": "business_id is required"},
                status_code=400,
            )

        if pc_id and pc_id in _active_connections:
            connection = _active_connections[pc_id]
            await connection.renegotiate(
                sdp=offer["sdp"],
                type=offer["type"],
                restart_pc=offer.get("restart_pc", False),
            )
        else:
            connection = SmallWebRTCConnection()
            await connection.initialize(sdp=offer["sdp"], type=offer["type"])

            @connection.event_handler("closed")
            async def _on_closed(conn):
                _active_connections.pop(conn.pc_id, None)

            transport = SmallWebRTCTransport(
                webrtc_connection=connection,
                params=TransportParams(
                    audio_in_enabled=True,
                    audio_out_enabled=True,
                    vad_enabled=True,
                    vad_audio_passthrough=True,
                ),
            )

            _active_connections[connection.pc_id] = connection
            asyncio.create_task(run_webrtc_pipeline(transport, business_id))

        answer = connection.get_answer()  # sync — no await
        return JSONResponse(content=answer)

    except Exception as e:
        print(f"Fatal WebRTC setup exception: {e}")
        return JSONResponse(
            content={"error": "Failed to establish WebRTC connection"},
            status_code=500,
        )