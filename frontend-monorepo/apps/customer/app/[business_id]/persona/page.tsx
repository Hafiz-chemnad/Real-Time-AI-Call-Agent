'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useWorkspaceStore } from '@/store/workspace';
import { useForm } from 'react-hook-form';
import { Plus, X, ShieldAlert, Loader2, Check } from 'lucide-react';

interface PersonaForm {
  prompt: string;
  strictScope: boolean;
  requireToolConfirm: boolean;
}

export default function PersonaPage({ params }: { params: { business_id: string } }) {
  const { activeBusinessId } = useWorkspaceStore();
  const currentId = activeBusinessId || params.business_id;
  const queryClient = useQueryClient();

  const [escalationChips, setEscalationChips] = useState<string[]>(['speak to human', 'manager']);
  const [chipInput, setChipInput] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);

  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const { register, handleSubmit, reset } = useForm<PersonaForm>();

  const { data, isLoading } = useQuery({
    queryKey: ['persona', currentId],
    queryFn: async () => {
      const res = await fetch(`${backendUrl}/businesses/${currentId}/persona`);
      if (!res.ok) {
        const mockData = {
          prompt: 'You are a helpful assistant for this dental clinic. Be polite and concise.',
          strictScope: true,
          requireToolConfirm: false,
          escalationTriggers: ['speak to human', 'manager'],
        };
        reset(mockData);
        setEscalationChips(mockData.escalationTriggers);
        return mockData;
      }
      const data = await res.json();
      reset(data);
      if (data.escalationTriggers) setEscalationChips(data.escalationTriggers);
      return data;
    },
  });

  const saveMutation = useMutation({
    mutationFn: async (formData: PersonaForm) => {
      const res = await fetch(`${backendUrl}/businesses/${currentId}/persona`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...formData, escalationTriggers: escalationChips }),
      });
      if (!res.ok) throw new Error('Failed to save persona config');
      return res.json();
    },
    onSuccess: () => {
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
      queryClient.invalidateQueries({ queryKey: ['persona', currentId] });
    },
  });

  const handleAddChip = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && chipInput.trim() !== '') {
      e.preventDefault();
      if (!escalationChips.includes(chipInput.trim().toLowerCase())) {
        setEscalationChips([...escalationChips, chipInput.trim().toLowerCase()]);
      }
      setChipInput('');
    }
  };

  const removeChip = (chipToRemove: string) => {
    setEscalationChips(escalationChips.filter((chip) => chip !== chipToRemove));
  };

  if (isLoading) return <div className="animate-pulse w-full h-96 bg-slate/10 rounded-xl p-8" />;

  return (
    <div className="p-8 max-w-4xl space-y-8">
      <div>
        <h1 className="font-serif text-3xl text-ink font-bold mb-2">Persona & Guardrails</h1>
        <p className="text-slate">Configure how your AI behaves and when it should escalate to a human.</p>
      </div>

      <form onSubmit={handleSubmit((data) => saveMutation.mutate(data))} className="space-y-8">
        <div className="space-y-3">
          <label className="font-sans font-semibold text-ink">System Prompt</label>
          <textarea
            {...register('prompt')}
            rows={6}
            className="w-full bg-white border border-slate-custom rounded-xl p-4 font-mono text-sm text-ink focus:outline-none focus:ring-2 focus:ring-confirm-green shadow-sm"
            placeholder="You are a helpful assistant..."
          />
        </div>

        <div className="bg-white border border-slate-custom rounded-xl p-6 shadow-sm space-y-4">
          <h2 className="font-serif text-xl text-ink font-semibold flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-alert-coral" />
            Safety Guardrails
          </h2>

          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" {...register('strictScope')} className="w-5 h-5 accent-confirm-green" />
            <span className="text-ink font-medium">Strict Scope Limit (Do not answer off-topic questions)</span>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" {...register('requireToolConfirm')} className="w-5 h-5 accent-confirm-green" />
            <span className="text-ink font-medium">Require human confirmation before background actions</span>
          </label>
        </div>

        <div className="space-y-3">
          <label className="font-sans font-semibold text-ink">Escalation Triggers</label>
          <p className="text-sm text-slate">Type a phrase and press Enter to add. If the AI detects these phrases, it routes the call to a human.</p>

          <div className="flex flex-wrap gap-2 mb-3">
            {escalationChips.map((chip) => (
              <span key={chip} className="bg-alert-coral text-paper px-3 py-1 rounded-full text-sm font-mono flex items-center gap-2 shadow-sm">
                {chip}
                <button type="button" onClick={() => removeChip(chip)} className="hover:text-ink transition-colors">
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>

          <div className="relative">
            <Plus className="absolute left-3 top-3 w-5 h-5 text-slate" />
            <input
              type="text"
              value={chipInput}
              onChange={(e) => setChipInput(e.target.value)}
              onKeyDown={handleAddChip}
              placeholder="e.g. 'speak to human'"
              className="w-full bg-white border border-slate-custom rounded-xl py-3 pl-10 pr-4 font-mono text-sm text-ink focus:outline-none focus:ring-2 focus:ring-alert-coral shadow-sm"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={saveMutation.isPending}
          className="bg-confirm-green text-paper px-6 py-3 rounded-xl font-medium shadow-md hover:opacity-90 transition-opacity flex items-center gap-2"
        >
          {saveMutation.isPending ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : saveSuccess ? (
            <>
              <Check className="w-5 h-5" /> Saved!
            </>
          ) : (
            'Save Configuration'
          )}
        </button>
      </form>
    </div>
  );
}