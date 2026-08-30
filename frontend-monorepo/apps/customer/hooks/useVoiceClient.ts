'use client';

import { useState, useRef, useCallback } from 'react';

type VoiceState = 'idle' | 'listening' | 'thinking' | 'speaking';

export function useVoiceClient(businessId?: string) {
  const [state, setState] = useState<VoiceState>('idle');
  const [isConnected, setIsConnected] = useState(false);

  const pcRef = useRef<RTCPeerConnection | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioElRef = useRef<HTMLAudioElement | null>(null);
  const pcIdRef = useRef<string | null>(null);

  const stopSession = useCallback(() => {
    if (pcRef.current) {
      pcRef.current.close();
      pcRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (audioElRef.current) {
      audioElRef.current.srcObject = null;
      audioElRef.current = null;
    }
    pcIdRef.current = null;
    setIsConnected(false);
    setState('idle');
  }, []);

  const startSession = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
      });
      pcRef.current = pc;

      stream.getTracks().forEach((track) => pc.addTrack(track, stream));

      pc.ontrack = (event) => {
        if (!audioElRef.current) {
          audioElRef.current = new Audio();
          audioElRef.current.autoplay = true;
        }
        if (event.streams && event.streams[0]) {
          audioElRef.current.srcObject = event.streams[0];
        } else {
          audioElRef.current.srcObject = new MediaStream([event.track]);
        }
        setState('speaking');
      };

      pc.oniceconnectionstatechange = () => {
        if (pc.iceConnectionState === 'connected') {
          setIsConnected(true);
          setState('listening');
        } else if (
          pc.iceConnectionState === 'disconnected' ||
          pc.iceConnectionState === 'failed' ||
          pc.iceConnectionState === 'closed'
        ) {
          stopSession();
        }
      };

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      await new Promise<void>((resolve) => {
        if (pc.iceGatheringState === 'complete') {
          resolve();
        } else {
          const checkState = () => {
            if (pc.iceGatheringState === 'complete') {
              pc.removeEventListener('icegatheringstatechange', checkState);
              resolve();
            }
          };
          pc.addEventListener('icegatheringstatechange', checkState);
        }
      });

      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const targetUrl = backendUrl.includes('proxy')
        ? `${backendUrl}/webrtc/connect`
        : `${backendUrl}/webrtc/connect`;

      const response = await fetch(targetUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sdp: pc.localDescription?.sdp,
          type: pc.localDescription?.type,
          pc_id: pcIdRef.current,
          business_id: businessId,
        }),
      });

      if (!response.ok) {
        throw new Error(`WebRTC setup failed: ${response.statusText}`);
      }

      const answer = await response.json();
      if (answer.pc_id) {
        pcIdRef.current = answer.pc_id;
      }

      await pc.setRemoteDescription(
        new RTCSessionDescription({
          type: answer.type,
          sdp: answer.sdp,
        })
      );
    } catch (err) {
      console.error('Voice WebRTC connection error:', err);
      stopSession();
    }
  }, [businessId, stopSession]);

  return { state, isConnected, startSession, stopSession };
}