'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useWorkspaceStore } from '@/store/workspace';

export default function RootPage() {
  const router = useRouter();
  const { activeBusinessId } = useWorkspaceStore();

  useEffect(() => {
    const tenantId = activeBusinessId || 'demo-business';
    router.replace(`/${tenantId}`);
  }, [activeBusinessId, router]);

  return (
    <div className="flex flex-1 items-center justify-center bg-paper min-h-screen">
      <div className="flex items-center gap-3">
        <div className="w-4 h-4 rounded-full bg-confirm-green animate-ping" />
        <p className="font-mono text-sm text-slate">Loading Business Workspace...</p>
      </div>
    </div>
  );
}
