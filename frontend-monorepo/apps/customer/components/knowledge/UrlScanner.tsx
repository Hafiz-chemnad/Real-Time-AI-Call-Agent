'use client';

import { useState } from 'react';
import { Globe, Loader2, CheckCircle } from 'lucide-react';
import { useWorkspaceStore } from '@/store/workspace';

export function UrlScanner() {
  const { activeBusinessId } = useWorkspaceStore();
  const [url, setUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [scanStatus, setScanStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const handleScan = async () => {
    if (!url) return;

    setIsScanning(true);
    setScanStatus('idle');
    setMessage('');

    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/knowledge/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          business_id: activeBusinessId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Scanner returned error status ${response.status}`);
      }

      setScanStatus('success');
      setMessage('Website scanned and knowledge embedded successfully!');
      setUrl('');
    } catch (err: any) {
      console.error('URL Scan error:', err);
      setScanStatus('error');
      setMessage(err.message || 'Failed to scan URL');
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto text-center space-y-6 mt-8">
      <div className="w-16 h-16 bg-paper rounded-full flex items-center justify-center mx-auto border border-slate-custom">
        {scanStatus === 'success' ? (
          <CheckCircle className="w-8 h-8 text-confirm-green" />
        ) : (
          <Globe className="w-8 h-8 text-ink" />
        )}
      </div>

      <h2 className="text-xl font-serif font-semibold text-ink">Scan your Website</h2>
      <p className="text-slate text-sm">
        Enter your URL and we will automatically scrape and embed your public pages.
      </p>

      <div className="flex gap-2">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://yourwebsite.com"
          className="flex-1 border border-slate-custom rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-confirm-green font-mono text-sm"
        />
        <button
          onClick={handleScan}
          disabled={isScanning || !url.trim()}
          className="bg-confirm-green text-paper px-6 py-3 rounded-xl font-medium shadow-md flex items-center gap-2 disabled:opacity-70"
        >
          {isScanning && <Loader2 className="w-4 h-4 animate-spin" />}
          Scan
        </button>
      </div>

      {message && (
        <p
          className={`text-sm mt-2 ${
            scanStatus === 'success' ? 'text-confirm-green' : 'text-red-500'
          }`}
        >
          {message}
        </p>
      )}
    </div>
  );
}