'use client';

import { useEffect, useState } from 'react';
import { XCircle, BrainCircuit, Loader2 } from 'lucide-react';

interface CallDetailSheetProps {
  logId: string;
  duration: string;
  onClose: () => void;
}

interface TranscriptTurn {
  speaker: 'caller' | 'agent' | 'user';
  text: string;
}

interface CallLogDetails {
  id: string;
  duration?: string;
  transcript?: TranscriptTurn[] | string;
  trace_logs?: string;
  internal_thoughts?: string;
  [key: string]: any;
}

export function CallDetailSheet({ logId, duration, onClose }: CallDetailSheetProps) {
  const [logData, setLogData] = useState<CallLogDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchLogDetail() {
      if (!logId) return;
      setIsLoading(true);
      setError(null);

      try {
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${backendUrl}/logs/${logId}`);

        if (!response.ok) {
          throw new Error(`Failed to fetch log details (Status ${response.status})`);
        }

        const data = await response.json();
        setLogData(data);
      } catch (err: any) {
        console.error('Failed to fetch call log details:', err);
        setError(err.message || 'Error fetching call log details');
      } finally {
        setIsLoading(false);
      }
    }

    fetchLogDetail();
  }, [logId]);

  const renderTranscript = () => {
    if (!logData?.transcript) {
      return (
        <p className="text-slate text-sm italic">No transcript recorded for this call.</p>
      );
    }

    if (typeof logData.transcript === 'string') {
      return (
        <div className="bg-paper text-ink p-3 rounded-xl border border-slate-custom font-mono text-sm whitespace-pre-wrap">
          {logData.transcript}
        </div>
      );
    }

    return logData.transcript.map((turn, idx) => {
      const isUser = turn.speaker === 'caller' || turn.speaker === 'user';
      return (
        <div
          key={idx}
          className={`flex flex-col gap-1 font-mono text-sm ${
            isUser ? 'self-start max-w-[80%]' : 'self-end max-w-[80%]'
          }`}
        >
          <span className={`text-xs text-slate ${isUser ? '' : 'text-right'}`}>
            {isUser ? 'Caller' : 'AI Agent'}
          </span>
          <div
            className={`p-3 rounded-2xl border border-slate-custom ${
              isUser
                ? 'bg-slate/10 text-ink rounded-tl-none'
                : 'bg-paper text-ink rounded-tr-none shadow-sm'
            }`}
          >
            {turn.text}
          </div>
        </div>
      );
    });
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full md:w-[500px] bg-white border-l border-slate-custom shadow-2xl z-50 flex flex-col transform transition-transform animate-in slide-in-from-right">
      <div className="p-6 border-b border-slate-custom flex justify-between items-center bg-paper">
        <div>
          <h2 className="font-serif font-bold text-xl text-ink">Call Transcript</h2>
          <p className="text-sm text-slate">{logId} • {logData?.duration || duration}</p>
        </div>
        <button onClick={onClose} className="text-slate hover:text-ink transition-colors">
          <XCircle className="w-6 h-6" />
        </button>
      </div>

      <div className="p-6 flex-1 overflow-y-auto space-y-6">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-confirm-green" />
            <p className="text-sm">Loading transcript...</p>
          </div>
        ) : error ? (
          <div className="p-4 bg-red-50 border border-red-200 text-red-600 rounded-xl text-sm">
            {error}
          </div>
        ) : (
          <>
            <div className="flex flex-col gap-4 font-mono text-sm">
              {renderTranscript()}
            </div>

            <div className="mt-8 border border-slate-custom rounded-xl overflow-hidden">
              <div className="bg-paper p-3 border-b border-slate-custom flex items-center gap-2 font-medium text-ink">
                <BrainCircuit className="w-4 h-4 text-line-amber" />
                AI Internal Thoughts & Tool Calls
              </div>
              <div className="p-4 bg-ink text-confirm-green font-mono text-xs whitespace-pre-wrap">
                {logData?.trace_logs || logData?.internal_thoughts || `[STATUS]: Log retrieved successfully\n[DETAILS]: Standard call execution completed.`}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}