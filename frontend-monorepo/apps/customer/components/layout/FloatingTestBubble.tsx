'use client';

import { useState } from 'react';
import { useWorkspaceStore } from '@/store/workspace';
import { useVoiceClient } from '@/hooks/useVoiceClient';
import { Mic, X, Volume2, Loader2 } from 'lucide-react';

export function FloatingTestBubble() {
  const [isOpen, setIsOpen] = useState(false);
  const { activeBusinessId } = useWorkspaceStore();
  const { state, isConnected, startSession, stopSession } = useVoiceClient(activeBusinessId);

  const handleToggleModal = () => {
    if (isOpen) {
      stopSession();
      setIsOpen(false);
    } else {
      setIsOpen(true);
    }
  };

  return (
    <>
      <button
        onClick={handleToggleModal}
        className="fixed bottom-6 right-6 z-50 flex items-center gap-3 bg-ink text-paper px-5 py-3 rounded-full shadow-2xl hover:scale-105 transition-all border border-slate-custom"
      >
        <div className="relative flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-line-amber opacity-75" />
          <span className="relative inline-flex rounded-full h-3 w-3 bg-line-amber" />
        </div>
        <span className="font-sans font-medium text-sm">Test AI Agent</span>
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-paper border border-slate-custom rounded-2xl p-8 max-w-sm w-full flex flex-col items-center gap-6 relative shadow-2xl">
            <button
              onClick={handleToggleModal}
              className="absolute top-4 right-4 text-slate hover:text-ink p-1 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>

            <h3 className="font-serif font-semibold text-xl text-ink">Voice Sandbox</h3>
            
            <div className="relative flex items-center justify-center w-36 h-36">
              <div
                className={`absolute inset-0 rounded-full transition-all duration-500 ${
                  state === 'listening'
                    ? 'bg-line-amber/30 animate-ping'
                    : state === 'speaking'
                    ? 'bg-confirm-green/30 animate-pulse'
                    : 'bg-slate/10'
                }`}
              />
              <div
                className={`w-28 h-28 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg ${
                  state === 'listening'
                    ? 'bg-line-amber text-ink scale-110'
                    : state === 'speaking'
                    ? 'bg-confirm-green text-paper scale-105'
                    : state === 'thinking'
                    ? 'bg-ink text-paper'
                    : 'bg-slate/20 text-slate'
                }`}
              >
                {state === 'thinking' ? (
                  <Loader2 className="w-10 h-10 animate-spin" />
                ) : state === 'speaking' ? (
                  <Volume2 className="w-10 h-10 animate-bounce" />
                ) : (
                  <Mic className="w-10 h-10" />
                )}
              </div>
            </div>

            <div className="font-mono text-sm uppercase tracking-wider text-center">
              {!isConnected ? (
                <span className="text-slate">Click to initialize audio context</span>
              ) : state === 'listening' ? (
                <span className="text-line-amber font-semibold">Listening...</span>
              ) : state === 'thinking' ? (
                <span className="text-ink font-semibold">Thinking...</span>
              ) : (
                <span className="text-confirm-green font-semibold">Speaking...</span>
              )}
            </div>

            {!isConnected ? (
              <button
                onClick={startSession}
                className="w-full bg-confirm-green text-paper font-sans font-medium py-3 rounded-xl shadow hover:opacity-90 transition-all"
              >
                Start Test Session
              </button>
            ) : (
              <button
                onClick={stopSession}
                className="w-full bg-alert-coral text-paper font-sans font-medium py-3 rounded-xl shadow hover:opacity-90 transition-all"
              >
                End Test Session
              </button>
            )}
          </div>
        </div>
      )}
    </>
  );
}