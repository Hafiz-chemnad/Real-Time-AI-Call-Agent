'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useWorkspaceStore } from '@/store/workspace';
import { Globe, FileText, FileSpreadsheet, MessageSquarePlus, Loader2, Plus, Trash2, CheckCircle2 } from 'lucide-react';

type SearchMode = 'vectorless' | 'vector';

interface QAPair {
  id: string;
  question: string;
  answer: string;
}

export default function KnowledgePage({ params }: { params: { business_id: string } }) {
  const { activeBusinessId } = useWorkspaceStore();
  const businessId = activeBusinessId || params.business_id;
  const queryClient = useQueryClient();

  const [searchMode, setSearchMode] = useState<SearchMode>('vector');
  const [activeTab, setActiveTab] = useState<'web' | 'pdf' | 'csv' | 'qa'>('web');

  const [websiteUrl, setWebsiteUrl] = useState('');
  const [qaList, setQaList] = useState<QAPair[]>([
    { id: '1', question: 'What are your operating hours?', answer: 'We are open Monday to Friday, 9 AM to 5 PM EST.' },
  ]);
  const [newQuestion, setNewQuestion] = useState('');
  const [newAnswer, setNewAnswer] = useState('');

  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const scanWebsiteMutation = useMutation({
    mutationFn: async (url: string) => {
      const res = await fetch(`${backendUrl}/businesses/${businessId}/knowledge/scan-web`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, searchMode }),
      });
      if (!res.ok) throw new Error('Failed to start website scan');
      return res.json();
    },
  });

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>, fileType: 'pdf' | 'csv') => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const formData = new FormData();
    formData.append('file', files[0]);
    formData.append('type', fileType);
    formData.append('searchMode', searchMode);

    await fetch(`${backendUrl}/businesses/${businessId}/knowledge/upload`, {
      method: 'POST',
      body: formData,
    });
    queryClient.invalidateQueries({ queryKey: ['knowledge', businessId] });
  };

  const handleAddQA = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newQuestion.trim() || !newAnswer.trim()) return;
    setQaList([...qaList, { id: Date.now().toString(), question: newQuestion, answer: newAnswer }]);
    setNewQuestion('');
    setNewAnswer('');
  };

  const handleDeleteQA = (id: string) => {
    setQaList(qaList.filter((item) => item.id !== id));
  };

  return (
    <div className="p-8 max-w-5xl space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl text-ink font-bold mb-2">Knowledge Base</h1>
          <p className="text-slate">Upload data to train your AI on your specific business context.</p>
        </div>

        <div className="bg-white border border-slate-custom rounded-xl p-1 flex items-center shadow-sm">
          <button
            onClick={() => setSearchMode('vectorless')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              searchMode === 'vectorless' ? 'bg-ink text-paper shadow' : 'text-slate hover:text-ink'
            }`}
          >
            Fast Search (Vectorless)
          </button>
          <button
            onClick={() => setSearchMode('vector')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              searchMode === 'vector' ? 'bg-confirm-green text-paper shadow' : 'text-slate hover:text-ink'
            }`}
          >
            Deep Semantic (Vector)
          </button>
        </div>
      </div>

      <div className="flex gap-4 border-b border-slate-custom pb-4 overflow-x-auto">
        {[
          { id: 'web', label: 'Website Scanner', icon: Globe },
          { id: 'pdf', label: 'Document Upload', icon: FileText },
          { id: 'csv', label: 'Spreadsheets', icon: FileSpreadsheet },
          { id: 'qa', label: 'Q&A Flashcards', icon: MessageSquarePlus },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all whitespace-nowrap ${
                activeTab === tab.id ? 'bg-white shadow text-ink border border-slate-custom' : 'text-slate hover:bg-white/50'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div className="bg-white border border-slate-custom rounded-2xl p-8 shadow-sm min-h-[400px]">
        {activeTab === 'web' && (
          <div className="max-w-xl mx-auto text-center space-y-6 mt-8">
            <div className="w-16 h-16 bg-paper rounded-full flex items-center justify-center mx-auto border border-slate-custom">
              <Globe className="w-8 h-8 text-ink" />
            </div>
            <h2 className="text-xl font-serif font-semibold text-ink">Scan your Website</h2>
            <p className="text-slate text-sm">Enter your URL and we will automatically scrape and embed your public pages.</p>
            <div className="flex gap-2">
              <input
                type="url"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                placeholder="https://yourwebsite.com"
                className="flex-1 border border-slate-custom rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-confirm-green"
              />
              <button
                onClick={() => scanWebsiteMutation.mutate(websiteUrl)}
                disabled={scanWebsiteMutation.isPending || !websiteUrl}
                className="bg-confirm-green text-paper px-6 py-3 rounded-xl font-medium shadow-md flex items-center gap-2 hover:opacity-90 disabled:opacity-50"
              >
                {scanWebsiteMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Scan'}
              </button>
            </div>
            {scanWebsiteMutation.isSuccess && (
              <p className="text-confirm-green text-sm flex items-center justify-center gap-1">
                <CheckCircle2 className="w-4 h-4" /> Website scan started successfully.
              </p>
            )}
          </div>
        )}

        {activeTab === 'pdf' && (
          <div className="max-w-xl mx-auto mt-8">
            <label className="border-2 border-dashed border-slate-custom rounded-2xl p-12 text-center hover:bg-paper/50 transition-colors cursor-pointer block">
              <FileText className="w-12 h-12 text-slate mx-auto mb-4" />
              <h3 className="text-lg font-medium text-ink mb-1">Upload PDF Documents</h3>
              <p className="text-slate text-sm">Click to select files to index</p>
              <input type="file" accept=".pdf" onChange={(e) => handleFileUpload(e, 'pdf')} className="hidden" />
            </label>
          </div>
        )}

        {activeTab === 'csv' && (
          <div className="max-w-xl mx-auto mt-8">
            <label className="border-2 border-dashed border-slate-custom rounded-2xl p-12 text-center hover:bg-paper/50 transition-colors cursor-pointer block">
              <FileSpreadsheet className="w-12 h-12 text-slate mx-auto mb-4" />
              <h3 className="text-lg font-medium text-ink mb-1">Upload CSV or Excel Spreadsheets</h3>
              <p className="text-slate text-sm">Click to index tabular data</p>
              <input type="file" accept=".csv, .xlsx" onChange={(e) => handleFileUpload(e, 'csv')} className="hidden" />
            </label>
          </div>
        )}

        {activeTab === 'qa' && (
          <div className="max-w-2xl mx-auto space-y-6">
            <form onSubmit={handleAddQA} className="p-4 bg-paper rounded-xl border border-slate-custom space-y-3">
              <h3 className="font-semibold text-ink text-sm">Add Question & Answer Pair</h3>
              <input
                type="text"
                placeholder="Question (e.g. What is your refund policy?)"
                value={newQuestion}
                onChange={(e) => setNewQuestion(e.target.value)}
                className="w-full border border-slate-custom rounded-lg p-2.5 text-sm"
              />
              <textarea
                placeholder="Answer..."
                value={newAnswer}
                onChange={(e) => setNewAnswer(e.target.value)}
                className="w-full border border-slate-custom rounded-lg p-2.5 text-sm"
                rows={2}
              />
              <button type="submit" className="bg-ink text-paper text-xs px-4 py-2 rounded-lg font-medium flex items-center gap-1">
                <Plus className="w-3.5 h-3.5" /> Save Q&A
              </button>
            </form>

            <div className="space-y-3">
              {qaList.map((item) => (
                <div key={item.id} className="p-4 border border-slate-custom rounded-xl flex justify-between items-start">
                  <div>
                    <h4 className="font-bold text-ink text-sm">{item.question}</h4>
                    <p className="text-slate text-sm mt-1">{item.answer}</p>
                  </div>
                  <button onClick={() => handleDeleteQA(item.id)} className="text-slate hover:text-alert-coral p-1">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}