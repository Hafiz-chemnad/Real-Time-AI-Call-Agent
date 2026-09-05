'use client';

import { useEffect, useState } from 'react';
import { useWorkspaceStore } from '@/store/workspace';
import { useQueryClient } from '@tanstack/react-query';
import { Building2, ChevronDown, Loader2 } from 'lucide-react';

interface BusinessItem {
  id: string;
  name: string;
}

export function WorkspaceSwitcher() {
  const { activeBusinessId, setActiveBusinessId } = useWorkspaceStore();
  const queryClient = useQueryClient();
  const [businesses, setBusinesses] = useState<BusinessItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadBusinesses() {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${backendUrl}/businesses`);
        if (response.ok) {
          const data = await response.json();
          if (Array.isArray(data) && data.length > 0) {
            setBusinesses(data);
            if (!activeBusinessId) {
              setActiveBusinessId(data[0].id, queryClient);
            }
          } else {
            setBusinesses([{ id: activeBusinessId || 'demo-business', name: 'Demo Business' }]);
          }
        }
      } catch (err) {
        console.error('Failed to load business list:', err);
        setBusinesses([{ id: activeBusinessId || 'demo-business', name: 'Demo Business' }]);
      } finally {
        setIsLoading(false);
      }
    }
    loadBusinesses();
  }, [queryClient, setActiveBusinessId]);

  const handleSwitch = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newId = e.target.value;
    setActiveBusinessId(newId, queryClient);
  };

  return (
    <div className="relative flex items-center bg-white border border-slate-custom rounded-xl p-2 shadow-sm min-w-[200px]">
      <Building2 className="w-5 h-5 text-slate ml-2 shrink-0" />
      {isLoading ? (
        <div className="flex items-center gap-2 pl-3 py-1 text-slate text-sm">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading...
        </div>
      ) : (
        <select
          value={activeBusinessId || ''}
          onChange={handleSwitch}
          className="appearance-none bg-transparent pl-3 pr-8 py-1 text-ink font-medium font-sans focus:outline-none cursor-pointer w-full text-sm"
        >
          {businesses.map((biz) => (
            <option key={biz.id} value={biz.id}>
              {biz.name || biz.id}
            </option>
          ))}
        </select>
      )}
      <ChevronDown className="w-4 h-4 text-slate absolute right-3 pointer-events-none" />
    </div>
  );
}