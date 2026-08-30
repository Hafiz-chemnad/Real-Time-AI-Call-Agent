'use client';
import { use } from 'react';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useWorkspaceStore } from '@/store/workspace';
import { CreditCard, Download, Zap, Loader2, CheckCircle2 } from 'lucide-react';

interface Invoice {
  id: string;
  date: string;
  amount: string;
  status: 'Paid' | 'Pending' | 'Failed';
  pdfUrl?: string;
}

interface BillingInfo {
  autoRefill: boolean;
  minutesRemaining: number;
  totalMinutes: number;
  invoices: Invoice[];
}

export default function BillingPage({ params }: { params: { business_id: string } }) {
  const { activeBusinessId } = useWorkspaceStore();
  const businessId = activeBusinessId || params.business_id;
  const queryClient = useQueryClient();

  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const { data: billing, isLoading } = useQuery<BillingInfo>({
    queryKey: ['billing', businessId],
    queryFn: async () => {
      const res = await fetch(`${backendUrl}/businesses/${businessId}/billing`);
      if (!res.ok) {
        return {
          autoRefill: true,
          minutesRemaining: 184,
          totalMinutes: 500,
          invoices: [
            { id: 'INV-001', date: 'Oct 01, 2024', amount: '$49.00', status: 'Paid' },
            { id: 'INV-002', date: 'Sep 01, 2024', amount: '$49.00', status: 'Paid' },
          ],
        };
      }
      return res.json();
    },
  });

  const toggleAutoRefillMutation = useMutation({
    mutationFn: async (newValue: boolean) => {
      const res = await fetch(`${backendUrl}/businesses/${businessId}/billing/auto-refill`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ autoRefill: newValue }),
      });
      if (!res.ok) throw new Error('Failed to update auto-refill setting');
      return res.json();
    },
    onMutate: async (newValue) => {
      await queryClient.cancelQueries({ queryKey: ['billing', businessId] });
      const previousBilling = queryClient.getQueryData<BillingInfo>(['billing', businessId]);
      if (previousBilling) {
        queryClient.setQueryData<BillingInfo>(['billing', businessId], {
          ...previousBilling,
          autoRefill: newValue,
        });
      }
      return { previousBilling };
    },
    onError: (_err, _newValue, context) => {
      if (context?.previousBilling) {
        queryClient.setQueryData(['billing', businessId], context.previousBilling);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['billing', businessId] });
    },
  });

  const handleDownloadInvoice = (invoiceId: string) => {
    window.open(`${backendUrl}/invoices/${invoiceId}/pdf`, '_blank');
  };

  const autoRefill = billing?.autoRefill ?? true;

  if (isLoading) {
    return (
      <div className="p-8 flex justify-center items-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-confirm-green" />
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl space-y-8">
      <div>
        <h1 className="font-serif text-3xl text-ink font-bold mb-2">Billing & Usage</h1>
        <p className="text-slate">Manage your payment methods, AI talk time refills, and invoices.</p>
      </div>

      <div className="bg-white border border-slate-custom rounded-2xl p-6 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="font-sans font-semibold text-lg text-ink flex items-center gap-2">
            <Zap className={`w-5 h-5 ${autoRefill ? 'text-line-amber' : 'text-slate'}`} />
            Auto-Refill AI Talk Time
          </h2>
          <p className="text-sm text-slate mt-1">Automatically purchase 100 minutes when balance drops below 20%.</p>
        </div>

        <button
          onClick={() => toggleAutoRefillMutation.mutate(!autoRefill)}
          disabled={toggleAutoRefillMutation.isPending}
          className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors focus:outline-none ${
            autoRefill ? 'bg-confirm-green' : 'bg-slate/30'
          }`}
        >
          <span
            className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${
              autoRefill ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </div>

      <div className="bg-white border border-slate-custom rounded-2xl shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-custom bg-paper">
          <h2 className="font-sans font-semibold text-lg text-ink flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-ink" />
            Invoice Ledger
          </h2>
        </div>
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-custom text-slate text-sm">
              <th className="p-4 font-medium">Date</th>
              <th className="p-4 font-medium">Amount</th>
              <th className="p-4 font-medium">Status</th>
              <th className="p-4 font-medium">Invoice</th>
            </tr>
          </thead>
          <tbody>
            {billing?.invoices?.map((invoice) => (
              <tr key={invoice.id} className="border-b border-slate-custom/50 hover:bg-paper/30 transition-colors">
                <td className="p-4 text-ink font-medium">{invoice.date}</td>
                <td className="p-4 font-mono text-ink">{invoice.amount}</td>
                <td className="p-4">
                  <span className="px-3 py-1 rounded-full text-xs font-semibold text-confirm-green bg-confirm-green/10">
                    {invoice.status}
                  </span>
                </td>
                <td className="p-4">
                  <button
                    onClick={() => handleDownloadInvoice(invoice.id)}
                    className="text-slate hover:text-ink flex items-center gap-1 text-sm font-medium transition-colors"
                  >
                    <Download className="w-4 h-4" /> PDF
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}