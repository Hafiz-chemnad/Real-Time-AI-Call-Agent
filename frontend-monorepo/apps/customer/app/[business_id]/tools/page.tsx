'use client';

import { useState } from 'react';
import { Wrench, Calendar, Lock, Webhook, MessageSquare, Check, Loader2 } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useWorkspaceStore } from '@/store/workspace';

export default function ToolsPage({ params }: { params: { business_id: string } }) {
  const { activeBusinessId } = useWorkspaceStore();
  const businessId = activeBusinessId || params.business_id;
  const queryClient = useQueryClient();

  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [showCalModal, setShowCalModal] = useState(false);
  const [bookingLink, setBookingLink] = useState('');

  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const { data: toolsConfig, isLoading } = useQuery({
    queryKey: ['tools', businessId],
    queryFn: async () => {
      const res = await fetch(`${backendUrl}/businesses/${businessId}/tools/`);
      if (!res.ok) {
        return {
          appointmentBooking: { active: true, link: 'https://cal.com/dentist/30min' },
          webhooks: { active: false },
        };
      }
      return res.json();
    },
  });

  const saveToolMutation = useMutation({
    mutationFn: async (payload: any) => {
      const res = await fetch(`${backendUrl}/businesses/${businessId}/tools/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Failed to update tool config');
      return res.json();
    },
    onSuccess: () => {
      setShowCalModal(false);
      queryClient.invalidateQueries({ queryKey: ['tools', businessId] });
    },
  });

  return (
    <div className="p-8 max-w-5xl space-y-8">
      <div>
        <h1 className="font-serif text-3xl text-ink font-bold mb-2">Tools & Skills</h1>
        <p className="text-slate">Equip your AI with integrations to take action during and after calls.</p>
      </div>

      <section className="space-y-4">
        <h2 className="font-sans font-semibold text-lg text-ink flex items-center gap-2 border-b border-slate-custom pb-2">
          <MessageSquare className="w-5 h-5 text-confirm-green" />
          Conversational Actions
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            onClick={() => setShowCalModal(true)}
            className="bg-white border border-slate-custom rounded-xl p-6 shadow-sm hover:shadow transition-shadow cursor-pointer"
          >
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-paper rounded-lg border border-slate-custom">
                <Calendar className="w-6 h-6 text-ink" />
              </div>
              <span className="bg-confirm-green/10 text-confirm-green text-xs font-bold px-2 py-1 rounded-md">ACTIVE</span>
            </div>
            <h3 className="font-semibold text-ink mb-1">Book Appointments</h3>
            <p className="text-sm text-slate">Connect to Cal.com or Calendly to let the AI schedule meetings live on the phone.</p>
          </div>
        </div>
      </section>

      <section className="space-y-4 pt-4">
        <h2 className="font-sans font-semibold text-lg text-ink flex items-center gap-2 border-b border-slate-custom pb-2">
          <Wrench className="w-5 h-5 text-slate" />
          Background Automations
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            onClick={() => setShowUpgradeModal(true)}
            className="bg-paper border border-slate-custom rounded-xl p-6 opacity-75 hover:opacity-100 transition-opacity cursor-pointer relative overflow-hidden"
          >
            <div className="absolute top-4 right-4 text-slate">
              <Lock className="w-5 h-5" />
            </div>
            <div className="p-3 bg-white rounded-lg border border-slate-custom w-fit mb-4">
              <Webhook className="w-6 h-6 text-slate" />
            </div>
            <h3 className="font-semibold text-slate mb-1">Custom Webhooks</h3>
            <p className="text-sm text-slate">Send post-call summaries and structured data payloads directly to your CRM.</p>
          </div>
        </div>
      </section>

      {showCalModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-white border border-slate-custom rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="font-serif font-semibold text-xl text-ink">Configure Calendar Booking</h3>
            <p className="text-slate text-sm">Paste your Cal.com or Calendly URL below:</p>
            <input
              type="url"
              placeholder="https://cal.com/your-name/30min"
              value={bookingLink || toolsConfig?.appointmentBooking?.link || ''}
              onChange={(e) => setBookingLink(e.target.value)}
              className="w-full border border-slate-custom rounded-xl p-3 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-confirm-green"
            />
            <div className="flex gap-3 pt-2">
              <button
                onClick={() => setShowCalModal(false)}
                className="flex-1 bg-paper text-ink font-medium py-2 rounded-xl border border-slate-custom hover:bg-slate/10"
              >
                Cancel
              </button>
              <button
                onClick={() => saveToolMutation.mutate({ appointmentBooking: { active: true, link: bookingLink } })}
                disabled={saveToolMutation.isPending}
                className="flex-1 bg-confirm-green text-paper font-medium py-2 rounded-xl shadow-md hover:opacity-90 flex items-center justify-center gap-1"
              >
                {saveToolMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save Integration'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showUpgradeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-white border border-slate-custom rounded-2xl p-8 max-w-sm w-full text-center shadow-2xl">
            <Lock className="w-12 h-12 text-line-amber mx-auto mb-4" />
            <h3 className="font-serif font-semibold text-xl text-ink mb-2">Upgrade to Pro</h3>
            <p className="text-slate text-sm mb-6">Custom Webhooks are a premium feature. Upgrade your plan to unlock powerful background automations.</p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowUpgradeModal(false)}
                className="flex-1 bg-paper text-ink font-medium py-2 rounded-xl border border-slate-custom hover:bg-slate/10"
              >
                Cancel
              </button>
              <button className="flex-1 bg-confirm-green text-paper font-medium py-2 rounded-xl shadow-md hover:opacity-90">
                View Plans
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}