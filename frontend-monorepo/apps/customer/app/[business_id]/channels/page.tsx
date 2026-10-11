'use client';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useWorkspaceStore } from '@/store/workspace';
import { Phone, Search, ArrowRightCircle, Loader2, Check, PlusCircle } from 'lucide-react';

interface AvailableNumber {
  phoneNumber: string;
  location: string;
}

interface ChannelConfig {
  claimedNumbers: string[];
  forwardingNumber: string;
}

export default function ChannelsPage({ params }: { params: { business_id: string } }) {
  const { activeBusinessId } = useWorkspaceStore();
  const businessId = activeBusinessId || params.business_id;
  const queryClient = useQueryClient();

  const [areaCode, setAreaCode] = useState('');
  const [forwardingInput, setForwardingInput] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);

  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const { data: channelData, isLoading: isLoadingChannels } = useQuery<ChannelConfig>({
    queryKey: ['channels', businessId],
    queryFn: async () => {
      const res = await fetch(`${backendUrl}/businesses/${businessId}/channels`);
      if (!res.ok) {
        return {
          claimedNumbers: ['+1 (415) 890-1234'],
          forwardingNumber: '+1 (555) 000-0000',
        };
      }
      const data = await res.json();
      setForwardingInput(data.forwardingNumber || '');
      return data;
    },
  });

  const {
    data: searchResults,
    isLoading: isSearching,
    refetch: searchNumbers,
  } = useQuery<AvailableNumber[]>({
    queryKey: ['searchNumbers', areaCode],
    queryFn: async () => {
      if (!areaCode || areaCode.length < 3) return [];
      const res = await fetch(`${backendUrl}/telephony/available-numbers?areaCode=${areaCode}`);
      if (!res.ok) {
        return [
          { phoneNumber: `+1 (${areaCode}) 555-0192`, location: 'San Francisco, CA' },
          { phoneNumber: `+1 (${areaCode}) 555-0148`, location: 'San Francisco, CA' },
        ];
      }
      return res.json();
    },
    enabled: false,
  });

  const claimNumberMutation = useMutation({
    mutationFn: async (phoneNumber: string) => {
      const res = await fetch(`${backendUrl}/businesses/${businessId}/channels/claim`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phoneNumber }),
      });
      if (!res.ok) throw new Error('Failed to claim number');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels', businessId] });
    },
  });

  const saveForwardingMutation = useMutation({
    mutationFn: async (number: string) => {
      const res = await fetch(`${backendUrl}/businesses/${businessId}/channels/forwarding`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ forwardingNumber: number }),
      });
      if (!res.ok) throw new Error('Failed to update forwarding number');
      return res.json();
    },
    onSuccess: () => {
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
      queryClient.invalidateQueries({ queryKey: ['channels', businessId] });
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (areaCode.length === 3) {
      searchNumbers();
    }
  };

  return (
    <div className="p-8 max-w-3xl space-y-8">
      <div>
        <h1 className="font-serif text-3xl text-ink font-bold mb-2">Phone Channels</h1>
        <p className="text-slate">Claim AI phone numbers and set up your call routing logic.</p>
      </div>

      <div className="bg-white border border-slate-custom rounded-2xl p-6 shadow-sm space-y-4">
        <h2 className="font-sans font-semibold text-lg text-ink flex items-center gap-2">
          <Phone className="w-5 h-5 text-ink" />
          Active AI Numbers
        </h2>
        {isLoadingChannels ? (
          <Loader2 className="w-5 h-5 animate-spin text-slate" />
        ) : (
          <div className="space-y-2">
            {channelData?.claimedNumbers?.map((num) => (
              <div key={num} className="flex justify-between items-center p-3 bg-paper rounded-xl border border-slate-custom font-mono text-sm">
                <span>{num}</span>
                <span className="text-xs font-semibold px-2 py-1 bg-confirm-green/10 text-confirm-green rounded-md">LIVE</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-white border border-slate-custom rounded-2xl p-6 shadow-sm space-y-4">
        <h2 className="font-sans font-semibold text-lg text-ink flex items-center gap-2">
          <PlusCircle className="w-5 h-5 text-ink" />
          Claim a New AI Number
        </h2>

        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3 w-5 h-5 text-slate" />
            <input
              type="text"
              placeholder="Enter local area code (e.g., 415)"
              value={areaCode}
              onChange={(e) => setAreaCode(e.target.value)}
              className="w-full border border-slate-custom rounded-xl py-3 pl-10 pr-4 font-mono focus:outline-none focus:ring-2 focus:ring-confirm-green"
              maxLength={3}
            />
          </div>
          <button
            type="submit"
            disabled={isSearching || areaCode.length !== 3}
            className="bg-ink text-paper px-6 py-3 rounded-xl font-medium shadow-md hover:bg-ink/90 transition-colors disabled:opacity-50"
          >
            {isSearching ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Search Numbers'}
          </button>
        </form>

        {searchResults && searchResults.length > 0 && (
          <div className="mt-4 space-y-2 border-t border-slate-custom pt-4">
            <p className="text-xs text-slate font-medium uppercase">Available Phone Numbers</p>
            {searchResults.map((item) => (
              <div key={item.phoneNumber} className="flex items-center justify-between p-3 border border-slate-custom rounded-xl hover:bg-paper/50">
                <div>
                  <div className="font-mono text-sm font-bold text-ink">{item.phoneNumber}</div>
                  <div className="text-xs text-slate">{item.location}</div>
                </div>
                <button
                  onClick={() => claimNumberMutation.mutate(item.phoneNumber)}
                  disabled={claimNumberMutation.isPending}
                  className="bg-confirm-green text-paper text-xs font-medium px-4 py-2 rounded-lg shadow hover:opacity-90"
                >
                  {claimNumberMutation.isPending ? 'Claiming...' : 'Claim Number'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-white border border-slate-custom rounded-2xl p-6 shadow-sm space-y-4">
        <h2 className="font-sans font-semibold text-lg text-ink flex items-center gap-2">
          <ArrowRightCircle className="w-5 h-5 text-line-amber" />
          Call Forwarding & Escalation
        </h2>
        <p className="text-sm text-slate">If the AI fails or the caller requests a human, route the call here.</p>

        <div className="space-y-3 pt-2">
          <label className="font-medium text-ink text-sm">Destination Phone Number</label>
          <input
            type="tel"
            placeholder="+1 (555) 000-0000"
            value={forwardingInput}
            onChange={(e) => setForwardingInput(e.target.value)}
            className="w-full border border-slate-custom rounded-xl py-3 px-4 font-mono text-ink focus:outline-none focus:ring-2 focus:ring-confirm-green"
          />
        </div>
        <button
          onClick={() => saveForwardingMutation.mutate(forwardingInput)}
          disabled={saveForwardingMutation.isPending}
          className="bg-confirm-green text-paper px-6 py-3 rounded-xl font-medium shadow-md mt-2 flex items-center gap-2 hover:opacity-90"
        >
          {saveForwardingMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : saveSuccess ? (
            <>
              <Check className="w-4 h-4" /> Saved!
            </>
          ) : (
            'Save Routing Config'
          )}
        </button>
      </div>
    </div>
  );
}