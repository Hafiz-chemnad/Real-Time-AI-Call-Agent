'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useWorkspaceStore } from '@/store/workspace';
import { Loader2, AlertCircle } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { setActiveBusinessId } = useWorkspaceStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch(`${backendUrl}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.message || 'Invalid email or password.');
      }

      const data = await res.json();
      const targetBusinessId = data.businessId || 'demo-business';

      // Persist active workspace in store and navigate
      setActiveBusinessId(targetBusinessId);
      router.replace(`/${targetBusinessId}`);
    } catch (err: any) {
      // Fallback for development/demo testing if backend is unreachable
      if (process.env.NODE_ENV === 'development' && email && password) {
        setActiveBusinessId('demo-business');
        router.replace('/demo-business');
        return;
      }
      setError(err.message || 'Authentication failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-paper p-4">
      <div className="bg-white border border-slate-custom rounded-2xl p-8 max-w-md w-full shadow-lg space-y-6">
        <div className="text-center space-y-2">
          <div className="h-12 w-12 mx-auto rounded-xl bg-confirm-green font-serif font-bold text-2xl text-paper flex items-center justify-center shadow-sm">
            V
          </div>
          <h1 className="font-serif text-2xl text-ink font-bold">Welcome Back</h1>
          <p className="text-slate text-sm">Sign in to manage your AI agents.</p>
        </div>

        {error && (
          <div className="p-3 bg-alert-coral/10 border border-alert-coral/20 rounded-xl flex items-center gap-2 text-alert-coral text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-semibold text-ink">Email</label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-slate-custom rounded-xl py-2.5 px-3 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-confirm-green"
              placeholder="name@company.com"
              required
            />
          </div>
          <div className="space-y-1">
            <label className="text-sm font-semibold text-ink">Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-slate-custom rounded-xl py-2.5 px-3 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-confirm-green"
              placeholder="••••••••"
              required
            />
          </div>
          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full bg-ink text-paper py-3 rounded-xl font-medium shadow-md hover:opacity-90 transition-opacity flex items-center justify-center gap-2 disabled:opacity-60"
          >
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}