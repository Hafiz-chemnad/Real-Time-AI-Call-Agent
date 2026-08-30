'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useWorkspaceStore } from '@/store/workspace';
import { Clock, Loader2 } from 'lucide-react';
import { CallDetailSheet } from '@/components/logs/CallDetailSheet';

type CallLog = {
  id: string;
  time: string;
  duration: string;
  outcome: 'Completed' | 'Escalated' | 'Failed';
  faithfulnessScore: number;
  relevancyScore: number;
};

export default function LogsPage({ params }: { params: { business_id: string } }) {
  const { activeBusinessId } = useWorkspaceStore();
  const businessId = activeBusinessId || params.business_id;
  const [selectedLog, setSelectedLog] = useState<CallLog | null>(null);

  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const { data: logs, isLoading, refetch } = useQuery<CallLog[]>({
    queryKey: ['logs', businessId],
    queryFn: async () => {
      const res = await fetch(`${backendUrl}/businesses/${businessId}/logs`);
      if (!res.ok) {
        return [
          { id: 'CALL_101', time: '10:45 AM', duration: '3m 12s', outcome: 'Completed', faithfulnessScore: 98, relevancyScore: 95 },
          { id: 'CALL_102', time: '11:20 AM', duration: '1m 05s', outcome: 'Escalated', faithfulnessScore: 82, relevancyScore: 60 },
          { id: 'CALL_103', time: '11:45 AM', duration: '0m 45s', outcome: 'Failed', faithfulnessScore: 0, relevancyScore: 0 },
        ];
      }
      return res.json();
    },
  });

  const outcomeColor = (outcome: string) => {
    if (outcome === 'Completed') return 'text-confirm-green bg-confirm-green/10';
    if (outcome === 'Escalated') return 'text-line-amber bg-line-amber/10';
    return 'text-alert-coral bg-alert-coral/10';
  };

  return (
    <div className="p-8 space-y-6 relative flex-1 flex flex-col">
      <h1 className="font-serif text-3xl text-ink font-bold">Call Logs & Analytics</h1>

      <div className="bg-white border border-slate-custom rounded-2xl shadow-sm overflow-hidden flex-1">
        {isLoading ? (
          <div className="p-12 flex items-center justify-center gap-3 text-slate">
            <Loader2 className="w-6 h-6 animate-spin text-confirm-green" />
            <span>Loading call logs...</span>
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-paper border-b border-slate-custom text-slate text-sm">
                <th className="p-4 font-medium">Time</th>
                <th className="p-4 font-medium">Duration</th>
                <th className="p-4 font-medium">Outcome</th>
                <th className="p-4 font-medium">Eval Scores</th>
              </tr>
            </thead>
            <tbody>
              {logs?.map((log) => (
                <tr
                  key={log.id}
                  onClick={() => setSelectedLog(log)}
                  className="border-b border-slate-custom/50 hover:bg-paper/30 cursor-pointer transition-colors"
                >
                  <td className="p-4 text-ink font-medium">{log.time}</td>
                  <td className="p-4 text-slate">{log.duration}</td>
                  <td className="p-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${outcomeColor(log.outcome)}`}>
                      {log.outcome}
                    </span>
                  </td>
                  <td className="p-4 flex gap-2">
                    <span className="bg-ink text-paper text-xs px-2 py-1 rounded-md" title="Faithfulness">
                      F: {log.faithfulnessScore}%
                    </span>
                    <span className="bg-ink text-paper text-xs px-2 py-1 rounded-md" title="Relevancy">
                      R: {log.relevancyScore}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {!isLoading && logs?.length === 0 && (
          <div className="p-12 text-center flex flex-col items-center">
            <Clock className="w-12 h-12 text-slate mb-4" />
            <p className="text-ink font-bold text-lg">No calls recorded yet</p>
            <p className="text-slate mb-6">Once your agent takes a call, it will appear here.</p>
            <button onClick={() => refetch()} className="bg-confirm-green text-paper px-6 py-2 rounded-xl font-medium shadow">
              Refresh Logs
            </button>
          </div>
        )}
      </div>

      {selectedLog && (
        <CallDetailSheet
          logId={selectedLog.id}
          duration={selectedLog.duration}
          onClose={() => setSelectedLog(null)}
        />
      )}
    </div>
  );
}